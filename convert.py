#! /usr/bin/env python3.2
# -*- coding: UTF-8 -*-

# Posterous to Wintersmith Python 3 migration script
# Copyright 2013 by Abe Pazos

author = 'Your name goes here'

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# 1. Install wintersmith: https://github.com/jnordberg/wintersmith
# 2. Export and download your Posterous blog in zip format
# 3. Unpack the downloaded file
# 4. In the terminal, cd into the unpacked folder
# 5. type: wintersmith new wintersmith
#    this will create a new wintersmith blog in a folder called wintersmith
# 6. type: git clone https://github.com/hamoid/Posterous-to-Wintersmith.git
# 7. type: cd Posterous-to-Wintersmith
# 8. type: ./convert.py
#    This script will run and it will analyze your blog files and translate
#    them creating markdown files inside wintersmith/contents/ and copying
#    your media files from audio/ image/ and video/ to each post folder

# 9. If everything went well you no longer need this script. You can now
#    start working on your new blog by editing and cleaning up posts, writing
#    new ones, editing the desing and templates.

# 10. type: cd ..

# To preview your new blog, cd into wintersmith, then
# type: wintersmith preview

# To generate the full blog and save it to disk, cd into wintersmith and
# type: wintersmith build

# If you use build, it creates your full static blog inside wintersmith/build/
# You can then upload that folder to your server.

# I hope it works for you :) I just made this script for myself and thought
# someone else might use it or improve it.


# Important note: For me both preview and build were failing because I have too many
# posts and media. I solved this by doing some changes to Wintersmith. You can find
# my version at http://github.com/hamoid/wintersmith

# The problem was, as far as I know, that wintersmith tried to process all my files
# in parallel and it run into "too many open files" errors. I solved this by updating
# async to 0.2 and then using the new functions it provides to limit the amount of
# simultaneous operations (mapLimit). I set a limit of 5. I haven't tested
# performance improvements when using higher (or lower) values. In theory, this is
# a script you will run once in your life.


# Development notes

# The Posterous export file contains both xml and html versions of the blog.

# I tried to make this script process the xml files, but that did not work
# because the links to images, audio and video files are absolute (pointing
# to online resources). Finding links to the local media files afterwards
# is not a simple task.

# The html files do contain the correct local links, so that solves the
# problem with absolute links in the xml files, but the html is invalid
# (several tags are not closed), and this messes up the etree parser.
# The fixHtml() function takes care of fixing those html issues.

import re, os, sys, subprocess, cgi, time, shutil, html.parser
from lxml import etree

opt = re.MULTILINE + re.DOTALL + re.IGNORECASE

def readFile(path):
    try:
        f = open(path, encoding="utf-8")
        content = f.read()
        f.close()
        return content
    except:
        return ""

def writeFile(path, content):
    f = open(path, "w")
    f.write(content)
    f.close()
    print("%s written" % path)

def createDir(dirname):
    if not os.path.isdir(dirname):
        os.makedirs(dirname)
        print("Folder %s created" % dirname)

def getFileList(path, rx, includePath=True):
    result = []
    for currPath in os.listdir(path):
        if re.search(rx, currPath):
            if includePath:
                result.append(os.path.join(path, currPath))
            else:
                result.append(currPath)
    return result

# Replace strings using a replacement list (imitating php function)
def strtr(text, dic):
    regex = re.compile("(%s)" % "|".join(map(re.escape, dic.keys())))
    return regex.sub(lambda mo: str(dic[mo.string[mo.start():mo.end()]]), text)

# Repair html for correct parsing
def fixHtml(h):
    # Close unclosed tags, otherwise parsing fails
    h = re.sub(r'<img(.*?)>', r'<img\1 />', h, flags=opt)
    h = re.sub(r'<link(.*?)>', r'<link\1 />', h, flags=opt)
    h = re.sub(r'<meta(.*?)>', r'<meta\1 />', h, flags=opt)

    # Move the p tag: <p><div/> --> <div/><p>, otherwise text content is lost
    # when replacing the media div by the markdown version
    h = re.sub(r'<p><div(.*?)</div>', r'<div\1</div><p>', h, flags=opt)
    return h

# Convert Posterous media divs to markdown and
# copy media files to post folder
def mediaToMarkdown(block, path, divSearch, tag, attr, repl):
    divs = block.findall(divSearch)
    for div in divs:
        items = div.findall(tag)
        markdown = ""
        for item in items:
            # From path:
            #   remove ../../../
            sourcePath = item.get(attr).replace("../../../", "")
            #   remove initial NNNNNNNN- which posterous added to media files
            targetName = re.sub(r'^\d+-', "", os.path.basename(sourcePath))
            #   replace spaces by underscores
            targetName = re.sub(' ', '_', targetName)
            #   get rid of strange characters
            targetName = re.sub(r'[^a-zA-Z0-9_.-]', '', targetName)
            #   add path to post folder
            targetPath = os.path.join(path, targetName)

            # Build markdown text containing links to media
            markdown += repl % targetName

            # copy file to post folder if not already there
            if not os.path.isfile(targetPath):
                shutil.copy(sourcePath, targetPath)

        # Create temporary div including the markdown
        newDiv = etree.Element("div")
        newDiv.text = markdown + "\n"
        # Replace original media div with new div containing markdown
        div.getparent().replace(div, newDiv)

def createMdFiles():
    # use an html parser to remove html entities
    htmlparser = html.parser.HTMLParser()

    yearPaths = getFileList('../posts', '^\d\d\d\d$')
    for yearPath in yearPaths:
        monthPaths = getFileList(yearPath, '^\d\d$')
        for monthPath in monthPaths:
            htmlPaths = getFileList(monthPath, '\.html$')
            for htmlPath in htmlPaths:
                # Create folder for post
                newArticleFolderName = os.path.basename(htmlPath)
                newArticleFolderName = re.sub(r'\.html$', '', newArticleFolderName)
                newArticlePath = '../wintersmith/contents/articles/' + newArticleFolderName
                createDir(newArticlePath)

                # Read and parse HTML
                htmlContent = fixHtml(readFile(htmlPath))
                dom = etree.HTML(htmlContent) #.fromstring()
                body = dom.find('body')

                # Create markdown header
                header = body.find('.//div[@class="post_header"]')
                imdHeader  = "---\n"
                #   title
                title = header.find('h3')
                imdHeader += 'title: "%s"\n' % title.text.replace('"', '\\"')
                #   author
                imdHeader += "author: %s\n" % "Abe Pazos"
                #   template
                imdHeader += "template: %s\n" % "article.jade"
                #   time
                postTime = header.find('.//span[@class="post_time"]')
                t = time.strptime(postTime.text, "%B %d %Y, %I:%M %p")
                imdHeader += "date: %s\n" % time.strftime("%Y-%m-%d %H:%M", t)
                #   tags
                tags = body.find('.//div[@class="post_tags_list"]')
                imdHeader += "tags: %s\n" % (tags.text if tags is not None else '')
                imdHeader += "----\n\n"

                # Create markdown content
                post = body.find('.//div[@class="post_body"]')
                #   convert divs containing media inside post to markdown, copy media to post folder
                mediaToMarkdown(post, newArticlePath, './/div[@class="p_embed p_image_embed"]', 'img', 'src', "![Image](%s)\n")
                mediaToMarkdown(post, newArticlePath, './/div[@class="p_embed p_audio_embed"]', './/a', 'href', "[Listen](%s)\n")
                mediaToMarkdown(post, newArticlePath, './/div[@class="p_embed p_video_embed"]', './/a', 'href', "[Watch](%s)\n")
                #   convert post to string
                imdContent = etree.tostring(post, method='html', encoding='utf-8').decode('utf-8')
                #   get rid / translate html tags
                trans = {
                    '<p>' : "",
                    '</p>' : "\n\n",
                    '<p />' : "",

                    '<div>' : "",
                    '</div>' : "\n\n",

                    '<br />' : "\n",
                    '<br>' : "\n",

                    '<li>'  : '+ ',
                    '</li>' : '',

                    '<ul>'  : '',
                    '</ul>' : ''
                }
                imdContent = strtr(imdContent, trans)
                #   regex substitutions that strtr could not do (it does not do regex)
                imdContent = re.sub(r'<div class=.\w+.>', '', imdContent, flags=opt)
                #   replace html entities by characters: "&aacute;" becomes "á"
                imdContent = htmlparser.unescape(imdContent)
                #   don't allow more than two line breaks in a row
                imdContent = re.sub(r"\n\n+", "\n\n", imdContent, flags=opt)

                # Write the processed post in markdown format
                writeFile("%s/index.md" % newArticlePath, imdHeader + imdContent)

createMdFiles()

# Python tip. How to apply a function to each item in a list:
#shortFiles = list(map(lambda s: re.sub(r'\d+-', '', s), files))

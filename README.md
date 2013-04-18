Posterous-to-Wintersmith
========================

Python script to migrate a Posterous blog to Wintersmith (a nodejs-based static blogging system)

# How to use

1. Install wintersmith: https://github.com/jnordberg/wintersmith
2. Export and download your Posterous blog in zip format
3. Unpack the downloaded file
4. In the terminal, cd into the unpacked folder
5. type: wintersmith new wintersmith
   This will create a new wintersmith blog in a folder called wintersmith
6. type: git clone https://github.com/hamoid/Posterous-to-Wintersmith.git
7. type: cd Posterous-to-Wintersmith
8. type: ./convert.py
   This script will run and it will analyze your blog files and translate
   them creating markdown files inside wintersmith/contents/ and copying
   your media files from audio/ image/ and video/ to each post folder

9. If everything went well you no longer need this script. You can now
   start working on your new blog by editing and cleaning up posts, writing
   new ones, editing the desing and templates.

10. type: cd ..

# To preview your new blog

cd into wintersmith, then
type: wintersmith preview

# To generate the full blog and save it to disk

cd into wintersmith and
type: wintersmith build

If you use build, it creates your full static blog inside wintersmith/build/
You can then upload that folder to your server.

I hope it works for you :) I just made this script for myself and thought
someone else might use it or improve it.


# Important note

For me both preview and build were failing because I have too many
posts and media. I solved this by doing some changes to Wintersmith. You can find
my version at [github](http://github.com/hamoid/wintersmith)

The problem was, as far as I know, that wintersmith tried to process all my files
in parallel and it run into "too many open files" errors. I solved this by updating
async to 0.2 and then using the new functions it provides to limit the amount of
simultaneous operations (mapLimit). I set a limit of 5. I haven't tested
performance improvements when using higher (or lower) values. In theory, this is
a script you will run once in your life.

Update: Wintersmith 2.0 is coming: https://github.com/jnordberg/wintersmith/pull/100 
It solves the issue I was having with too many files open, and it's MUCH faster
building and previewing. It makes my changes to Wintersmith no longer necessary.


# Development notes

The Posterous export file contains both xml and html versions of the blog.

I tried to make this script process the xml files, but that did not work because the links to images, audio and video files are absolute (pointing to online resources). Finding links to the local media files afterwards is not a simple task.

The html files do contain the correct local links, so that solves the problem with absolute links in the xml files, but the html is invalid (several tags are not closed), and this messes up the etree parser. The fixHtml() function takes care of fixing those html issues.

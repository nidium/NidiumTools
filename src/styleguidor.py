#!/usr/bin/python

# Copyright 2016 Nidium Inc. All rights reserved.
# Use of this source code is governed by a MIT license
# that can be found in the LICENSE file

"""
Styleguidor: Rate c/c++ source files accourding to a styleguide

Simple script that goes over the directorys given as cmd arguments, and rates
each c/c++ file accourding to some regexes
"""

import sys, os, re, sre_constants

SCORE = 0.0
EXTENSIONS = ['.c', '.h', '.cpp']
IGNORES = ['third-party', '.git', 'build', 'gyp', 'port']
STYLES = {
    'indentation':  {'pattern': '^\t+', 
                    #Flame war bait
                     'text': 'Indentation should be with spaces not with tabs', 
                     'weight': 1.00},
    'line-too-long':{'pattern': '.{132,}', 
                     #pref: 80, have multiple split windows next to each other
                     'text': 'Line must not exceed 132 chars', 
                     'weight': 0.25},
    'surround-=':   {'pattern': '([^ \t]+[\|\+\-=]=)|([\|\+\-=]=[^ \t\s]+)', 
                     #Improved readability
                     'text': 'Spaces must surround =', 
                     'weight': 1},
    ';':            {'pattern': ';[a-zA-Z]', 
                     #Improved readablity
                     'text': 'Whitespace needed after a ;', 
                     'weight': 0.25},
    ';;':           {'pattern': ';;', 
                     #Clean up is prefferedreadablity
                     'text': 'Double ;',
                     'weight': 0.15},
 
    'return-(':     {'pattern': '\breturn\(', 
                     #Essential keyword
                     'text': 'Whitespace needed between return and parenthesis', 
                     'weight': 0.25},
    'if-(':         {'pattern': '\bif\(', 
                     #Essential keyword
                     'text': 'Whitespace needed between if and parenthesis', 
                     'weight': 0.25},
    'for-(':        {'pattern': '\bfor\(', 
                     #Essential keyword
                     'text': 'Whitespace needed between for and parenthesis', 
                     'weight': 0.25},
    'do-(':         {'pattern': '\bdo\(', 
                     #Essential keyword
                     'text': 'Whitespace needed between do and parenthesis', 
                     'weight': 0.25},
    'switch-(':     {'pattern': '\bswitch\(', 
                     #Essential keyword
                    'text': 'Whitespace needed between switch and paranthesis', 
                     'weight': 0.25},
    'while-(':      {'pattern': '\bwhile\(', 
                     #Essential keyword
                     'text': 'Whitespace needed between while and parenthesis', 
                     'weight': 0.25},
    'paren-accu':   {'pattern': '\){', 
                     #This makes a the end of condition and the start of a block
                     'text': 'Whitespace needed between ) and {', 
                     'weight': 0.25},
    'paren-start':  {'pattern': '\([ \t]', 
                     #This makes it obvious that the inside belongs together 
                     'text': 'Whitespace not allowed after a (', 
                     'weight': 0.25},
    'paren-end':    {'pattern': '[ \t]\)', 
                     #This makes it obvious that the inside belongs together 
                     'text': 'Whitespace not allowed before a )', 
                     'weight': 0.25},
    'space-after-comma':{'pattern': ',[^ \t\s]', 
                     #This improves readablity
                    'text': 'Whitespace must follow a comma', 
                    'weight': 0.5},
    'ends-with-space':{'pattern': '.*[ \t]+$', 
                     #This looks horrible in pacman mode
                     'text': 'No whitespace allowed at the end of line', 
                     'weight': 0.01},
    #'preproc-indent':{'pattern': '^([ \t]+#)|(#[ \t]+)', 
                     #Some compilers do not handle this correctly
    #                'text': 'Indentation not allowed for directive', 
    #                'weight': 0.01},
}

def load():
    "setup the styles to a dict instead of a tuple)"
    IGNORES.insert(0, '.')
    for key, style in STYLES.items():
        try:
            style["re"] = re.compile(style['pattern'])
            style['score'] = 0.0 
        except sre_constants.error:
            print("Error in regex: " + key + ": '" + style['pattern'] + "'")
            sys.exit(1)

def usage():
    """Show the usage."""
    print("Usage: " + sys.argv[0] + " path1, [path2, ..]")
    sys.exit()

def process_file(path):
    "Read the file, process it line by line and show the improvements/rate"
    global SCORE
    ext = os.path.splitext(path)[1]
    if ext in EXTENSIONS:
        file_hd = open(path, 'r')
        line = ''
        line_nr = 0
        for line_nr, line in enumerate(file_hd.readlines()):
            for key, style in STYLES.items():
                result = style['re'].search(line)
                if result:
                    print(path + ":" + str(line_nr + 1) + "\t" + style['text'])
                    SCORE += style['weight']
                    STYLES[key]['score'] += style['weight']
        file_hd.close()
        if line != "\n":
            print(path + ":" + str(line_nr) + "\tDoes not end with a newline")
            SCORE += 1

def process_dir(path):
    "Process path if it is a file, else walk and process recursively"
    if os.path.isfile(path):
        process_file(path)
    else:
        for root, dirs, files in os.walk(path, topdown=True):
            for ign in IGNORES:
                if ign in dirs:
                    dirs.remove(ign)
            for name in files:
                fullpath = os.path.join(root, name)
                process_file(fullpath)

def show_score():
    "Display the score"
    print("\nThe code got a score of " + str(SCORE) + ".")

def main():
    """Start and run the files/dirs from the command line"""
    if len(sys.argv) == 1:
        usage()
    load()
    for arg in sys.argv[1::]:
        process_dir(arg)
    show_score()

if __name__ == '__main__':
    main()

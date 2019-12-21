from data import TEXT_DIR, UNZIPPED_DIR, is_x
import subprocess
import string
import re
import os

import logging
logger = logging.getLogger('delatex')


def pandoc_file(inputfile, outputfile):
    result = subprocess.run(
        ['pandoc', '--from', 'latex', '--to', 'markdown', '-s', '--atx-headers', inputfile, '-o', outputfile], capture_output=True)
    if result and result.returncode != 0:
        print(result.stderr.decode('utf-8', errors='ignore'))
        print(f'Error with file {inputfile}')

    return result.returncode


def pandoc(text: str) -> str:
    result = subprocess.run(['pandoc', '--from', 'latex', '--to', 'markdown',
                             '-s', '--atx-headers'], input=text, text=True, capture_output=True)
    if result and result.returncode != 0:
        print(result.stderr)
        print(f'Error with "{text[:30]}..."')

    return result.stdout


def detex_file(inputfile, outputfile):
    with open(inputfile, 'r') as fin:
        with open(outputfile, 'w') as fout:
            content = fin.read()
            output = detex(content)

            fout.write(output)


def detex(text: str) -> str:
    '''
    opendetex (https://github.com/pkubowicz/opendetex), installed via homebrew (brew install detex)
    '''

    try:
        result = subprocess.run(['detex', '-r'], text=True,
                                input=text, capture_output=True)
        return result.stdout
    except AttributeError:
        print(
            f"text {text[:16]} did not have attribute 'encode', which means it most likely wasn't a string (could be bytes).")
        return ''

# Chenhao's code
# START


class FinalContent:
    def __init__(self):
        self.result = []

    def appendString(self, text):
        self.result.append(text)
    # if tokenize then will add space between words

    def appendContent(self, content, pos, tokenize=False):
        if not tokenize:
            self.result.append(content[pos])
            return
        if content[pos] not in string.ascii_letters and content[pos] not in string.digits and content[pos] != '-':
            self.result.append(' %s' % content[pos])
            if pos < len(content) - 1 and content[pos + 1] != ' ':
                self.result.append(' ')
        else:
            self.result.append(content[pos])

    def getResult(self):
        return ''.join(self.result)


def getDebt(text):
    debt = 0
    for c in text:
        if c == '{':
            debt -= 1
        elif c == '}':
            debt += 1
    return debt


def removeDefinition(lines, content):
    debt = 0
    ignoreset = set(['def', 'newcommand', 'renewcommand',
                     'newtheorem', 'setsymbol', 'footmath'])
    for line in lines:
        pos = line.find('%')
        if pos != -1 and not (pos - 1 >= 0 and line[pos-1] == '\\'):
            line = line[0:pos]
        if len(line) == 0:
            continue
        pos = 0
        if line[pos] == '\\':
            pos += 1
            while pos < len(line) and (line[pos] in string.ascii_letters or line[pos] in string.digits):
                pos += 1
            latexcommand = line[1:pos]
            if latexcommand in ignoreset:
                debt = getDebt(line)
                continue
        if debt < 0:
            debt += getDebt(line)
            if debt <= 0:
                continue
        content.append('%s\n' % line.strip())


def removeBadMath(content):
    result = []
    pos = 0
    while pos < len(content) - 1:
        if content[pos:pos+2] == '\\(':
            if not (pos > 0 and content[pos-1] == '\\'):
                result.append(' $ ')
                pos += 2
                continue

        if content[pos:pos+2] == '\\)':
            if not (pos > 0 and content[pos-1] == '\\'):
                result.append(' $ ')
                pos += 2
                continue

        if content[pos:pos+2] == '\\[':
            if not (pos > 0 and content[pos-1] == '\\'):
                result.append(' $$ ')
                pos += 2
                continue

        if content[pos:pos+2] == '\\]':
            if not (pos > 0 and content[pos-1] == '\\'):
                result.append(' $$ ')
                pos += 2
                continue
        result.append(content[pos])
        pos += 1
    if pos < len(content):
        result.append(content[pos])
    return ''.join(result)


def simpleLatexToText(inputfile, outputfile, sectioned=False):
    '''
    Chenhao's latex to text algorithm.
    '''
    fin = open(inputfile)
    lines = fin.readlines()
    fin.close()
    content = []
    count = 0
    removeDefinition(lines, content)
    content = ''.join(content)
    content = removeBadMath(content)
    startpos = content.find('\\begin{document}')
    if startpos == -1:
        logger.warning('no start document %s', inputfile)
        return
    # sometimes title appear before document
    titlepos = content.find('\\title')
    if titlepos > 0 and titlepos < startpos:
        startpos = titlepos
    pos = startpos
    # label = 'document'
    ignoringmode = set(['equation', 'eqnarray', 'array', 'figure', 'align',
                        'table', 'tabular', 'math', 'displaymath', 'thebibliography'])
    wordpattern = re.compile(r'\w+')
    sectionmode = set(['section', 'section*', 'title'])
    finalcontent = FinalContent()
    title_end = -2
    while pos < len(content):
        if content[pos] == '\\':
            if content[pos+1:pos+5] == 'verb':
                tempInterval = 5
                if content[pos+6] == '*':
                    tempInterval = 6
                tempPos = pos + tempInterval
                while content[tempPos] == ' ':
                    tempPos += 1
                delim = content[tempPos]
                verbEnd = content.find(delim, tempPos + 1)
                for ti in range(tempPos + 1, verbEnd):
                    finalcontent.appendContent(content, ti)
                pos = verbEnd + 1

            elif content[pos+1] not in string.ascii_letters and content[pos+1] not in string.digits:
                if content[pos+1] == ' ':
                    pos += 1
                else:
                    pos += 2
            else:
                temppos = pos + 1
                while content[temppos] in string.ascii_letters or content[temppos] in string.digits:
                    temppos += 1
                latexcommand = content[pos+1:temppos]
                if latexcommand == 'begin':
                    # ignoring mode: equation, eqnarray, array, figure, align, table, tabular
                    modestart = content.find('{', pos)
                    modeend = content.find('}', pos)
                    mode = content[modestart+1:modeend]
                    modeword = re.findall(wordpattern, mode)
                    if modeword:
                        tomatchmode = modeword[0]
                    else:
                        tomatchmode = mode
                    if sectioned and tomatchmode == 'abstract':
                        finalcontent.appendString(
                            '\n###start section abstract###\n')
                    # print tomatchmode
                    if tomatchmode in ignoringmode or tomatchmode.find('bibliography') != -1:
                        if content.find('\\end{%s}' % mode, pos + 1) != -1:
                            pos = content.find(
                                '\\end{%s}' % mode, pos+1) + 6 + len(mode)
                        elif content.find('{%s}' % mode, pos + 1) != -1:
                            pos = content.find('{%s}' %
                                               mode, pos+1) + 2 + len(mode)
                        else:
                            pos = modeend + 1
                    else:
                        pos = modeend + 1
                elif latexcommand == 'end':
                    modestart = content.find('{', pos)
                    if modestart != -1:
                        modeend = content.find('}', pos)
                        pos = modeend + 1
                        if sectioned:
                            mode = content[modestart+1:modeend].lower()
                            if mode.strip() == 'abstract':
                                finalcontent.appendString(
                                    '\n###start dummy section###\n')
                    else:
                        pos += 1
                elif sectioned and latexcommand in sectionmode:
                    modestart = 0
                    if content[temppos] == '[':
                        temp = content.find(']', pos)
                        modestart = content.find('{', temp)
                    else:
                        modestart = content.find('{', pos)
                    pastparenthsis = 0
                    modeend = modestart
                    # find matching parathesis
                    while True:
                        modeend += 1
                        if content[modeend] == '}':
                            pastparenthsis -= 1
                            if pastparenthsis < 0:
                                break
                        elif content[modeend] == '{':
                            pastparenthsis += 1
                    mode = ''.join(
                        ['%s ' % a.strip() for a in content[modestart+1:modeend].splitlines()])
                    if latexcommand == 'title':
                        finalcontent.appendString(
                            '\n###start section title###\n')
                        title_end = modeend
                    else:
                        finalcontent.appendString(
                            '\n###start section %s###\n' % mode)
                    pos = temppos
                else:
                    pos = temppos
        elif content[pos] == '$':
            if content[pos+1] == '$':
                endpos = pos
                while True:
                    endpos = content.find('$$', endpos+2)
                    if content[endpos - 1] != '\\' or (content[endpos-1] == '\\' and content[endpos-2] == '\\'):
                        break
                    else:
                        endpos -= 1
                pos = endpos + 2
            else:
                endpos = pos
                while True:
                    endpos = content.find('$', endpos+1)
                    if content[endpos - 1] != '\\' or (content[endpos-1] == '\\' and content[endpos-2] == '\\'):
                        break
                pos = endpos + 1
        else:
            finalcontent.appendContent(content, pos)
            if sectioned and pos == title_end + 1:
                logger.info('title found %s %d %s', inputfile,
                            title_end, content[title_end + 1])
                finalcontent.appendString('\n###start section dummy###\n')
            pos += 1
        if pos < count:
            logger.error('find error %s %s %d %d %d', inputfile,
                         content[(count-100):count], count, len(content), pos)
            break
        else:
            count = pos
    fout = open(outputfile, 'w')
    lines = finalcontent.getResult().split('\n')
    logger.info('line number %d', len(lines))
    linenum = 0
    percent = 0.8
    for line in lines:
        linenum += 1
        if line.find('References') != -1 and linenum > percent * len(lines):
            break
        line = line.strip()
        words = line.split()
        for word in words:

            fout.write('%s ' % word)
        if line:
            fout.write('\n')
    fout.close()

# Chenhao's code
# END


def is_detexed(arxivid, versioncount) -> bool:
    return is_x(arxivid, versioncount, TEXT_DIR)


def main():
    '''
    Takes files from data/unzipped and converts them to text, then sends them to data/text.
    '''
    os.makedirs(TEXT_DIR, exist_ok=True)

    error_count = 0

    for sourcefile in os.listdir(UNZIPPED_DIR):
        sourcefilepath = os.path.join(UNZIPPED_DIR, sourcefile)
        outputfilepath = os.path.join(TEXT_DIR, sourcefile)
        result = pandoc_file(sourcefilepath, outputfilepath)

        if result != 0:
            error_count += 1

    print(f'Saw {error_count} errors.')


if __name__ == '__main__':
    main()

import codecs
import os


from icecake import cli, templates


def generate():

    output = '# -*- coding: utf-8 -*-\n\ntemplates = {\n'
    for filename in cli.ls_relative('templates'):
        contents = codecs.open(os.path.join('templates', filename), encoding='utf-8').read()
        output += '"%s":\n' % filename
        output += 'u"""' + contents + '""",\n'
    output += '}'


    f = codecs.open('icecake/templates.py', encoding='utf-8', mode='w')
    f.write(output)
    f.close()


if __name__ == '__main__':
    generate()

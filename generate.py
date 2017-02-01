import os


from icecake import cli, templates


def generate():

    output = 'templates = {\n'
    for filename in cli.ls_relative('templates'):
        contents = open(os.path.join('templates', filename)).read()
        output += '"%s":\n' % filename
        output += '"""' + contents + '""",\n'
    output += '}'


    f = open('templates.py', mode='w')
    f.write(output)
    f.close()


if __name__ == '__main__':
    generate()

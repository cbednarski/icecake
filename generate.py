import os


from icecake import icecake, templates


def generate():

    output = 'templates = {\n'
    for filename in icecake.ls_relative('templates'):
        contents = open(os.path.join('templates', filename)).read()
        output += '"%s":\n' % filename
        output += '"""' + contents + '""",\n'
    output += '}'


    f = open('templates.py', mode='w')
    f.write(output)
    f.close()


if __name__ == '__main__':
    generate()
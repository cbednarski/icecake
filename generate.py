import icecake

def generate():

    output = 'templates = {\n'
    for source_filename in icecake.Site.list_files('templates'):
        contents = open(source_filename).read()
        output += '"%s":\n' % source_filename
        output += '"""' + contents + '""",\n'
    output += '}'


    f = open('templates.py', mode='w')
    f.write(output)
    f.close()


if __name__ == '__main__':
    generate()
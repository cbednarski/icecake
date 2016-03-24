import icecake

def generate():

    templates = {}

    for source_filename in icecake.Site.list_files('../templates'):
        contents = open(source_filename).read()
        templates[source_filename] = contents

    output = 'templates = '+repr(templates)
    f = open('templates.py', mode='w')
    f.write(output)
    f.close()


if __name__ == '__main__':
    generate()
import icecake

def test_page():
	page = icecake.Page("this/file/does/not/exist.html")
	assert page.slug == "exist"
	assert page.folder == "this/file/does/not"
	assert page.ext == ".html"


def builder():
	import cuiBuilder
	reload(cuiBuilder)
	builder = cuiBuilder.CUIBuilder()
	builder.show()

def viewer():
	import cuiViewer
	reload(cuiViewer)
	viewer = cuiViewer.CUIViewer()
	viewer.show()
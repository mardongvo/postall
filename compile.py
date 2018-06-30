import sys
from distutils.core import setup
import py2exe

sys.path.insert(0, "C:\\Python27\\Lib\\site-packages\\reportlab")
setup(
	console=[{"script":"mainapp.py","icon_resources": [(0,"icon.ico")]}
	],
	options={
		"py2exe":{
			"packages": [
				'reportlab',
				'reportlab.graphics.charts',
				'reportlab.graphics.samples',
				'reportlab.graphics.widgets',
				'reportlab.graphics.barcode',
				'reportlab.graphics',
				'reportlab.lib',
				'reportlab.pdfbase',
				'reportlab.pdfgen',
				'reportlab.platypus',
			]
		}
	}	
)

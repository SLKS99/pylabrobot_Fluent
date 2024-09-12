from os.path import dirname, join

from sila2.framework import Feature

SiLAServiceFeature = Feature(open(join(dirname(__file__), "SiLAService.sila.xml")).read())

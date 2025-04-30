from setuptools import setup
import os
from glob import glob

package_name = 'yolo_color_tracker'

setup(
    name=package_name,
    version='1.0.0',
    packages=[package_name],
    data_files=[
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    author='Colby August',
    author_email='augusc@rpi.edu',
    description='YOLO detection + 3D Localization + LED control',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'detection_node = yolo_color_tracker.detection_node:main',
            'detection_3d_node = yolo_color_tracker.detection_3d_node:main',
            'tracking_node = yolo_color_tracker.tracking_node:main',
            'color_changer_service = yolo_color_tracker.color_changer_service:main',
        ],
    },
)


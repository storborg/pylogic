from setuptools import setup


setup(name='pylogic',
      version='0.0.1.dev',
      description='Tools for working with Saleae Logic.',
      long_description='',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
          # 'Programming Language :: Python :: 3.5',
          'Framework :: Pyramid',
      ],
      keywords='saleae logic analyzer',
      url='https://github.com/storborg/pylogic',
      author='Scott Torborg',
      author_email='storborg@gmail.com',
      install_requires=[
      ],
      license='MIT',
      packages=['pylogic'],
      include_package_data=True,
      entry_points=dict(console_scripts=[
      ]),
      zip_safe=False)

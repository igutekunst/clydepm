from clyde2.server import PackageServer, GerritPackageServer, TestServer
from clyde2.package import ClydePackage, TestPackage
from clyde2.resolver import resolve_package_dependencies, create_build_tree, get_frozen_packages
from clyde2.generators.ninja_build import generate_file

from clyde2.common import pprint_color, dict_contains, warn
from clyde2.rtems import get_rtems_cflags, get_rtems_cc
from termcolor import colored

from os.path import join
from os import getenv
import os

def build_package(path, 
                  traits = None, 
                  generator = None, fetch_remote = True,
                  frozen = False):
  if not generator:
    generator = generate_file

  if 'rtems' in traits and traits['rtems'] and 'CFLAGS' in os.environ:
    raise Exception("CFLAGS and --rtems specified. Please only specify one")

  extra_flags = ''
  if 'rtems' in traits and traits['rtems']:
    print ("Using RTEMS BSP: {0}".format(traits['rtems']))
    #extra_flags = get_rtems_cflags(traits['rtems'])


  elif 'CFLAGS' in os.environ:
    extra_flags = os.environ['CFLAGS']
    # Delete CFLAGS so they don't affect
    # foreign packages
    del os.environ['CFLAGS']
  



  if os.getenv('CC') and len(os.getenv('CC').split()) > 1:
    extra_flags = " ".join(os.getenv('CC').split()[1:]) + ' ' + extra_flags

  traits['cflags']  = ' ' + extra_flags + ' -fdiagnostics-color=always'

  top_package = ClydePackage(path, traits)
  server = GerritPackageServer(join(path, 'deps'))


  new_traits = traits.copy()



  if 'variant' in new_traits and new_traits['variant'] == 'test':
    del new_traits['variant']

  if not fetch_remote:
    warn("Only looking at local git tags")

  if frozen:
    print (colored("Using packages specified in versions.txt", 'yellow'))
    with open("versions.txt") as f:
      tuples = [line.strip().split("=") for line in f]
      frozen_packages = {tuple[0]: tuple[1] for tuple in tuples}
      packages = get_frozen_packages(frozen_packages, server, new_traits)
      
      # Add the top package since it's excluded from versions.txt
      packages.add(top_package)
  else:
    packages = resolve_package_dependencies(top_package, server, new_traits, fetch_remote)

  packages = {package.name:package for package in packages}

  if not frozen: 
    with open(join(path, 'versions.txt'),'w') as f:
      for name, package in packages.iteritems():
        if name != top_package.name:
          f.write("{0}={1}\n".format(name, package.version))
        package.inflate(packages)
  else:
    for name, package in packages.iteritems():
      print(colored("{0}={1}".format(name, package.version), 'green'))
      package.inflate(packages)



  tree = create_build_tree(top_package)
  rtems_makefile_path = None
  
  if getenv('CC'):
    compiler_prefix = getenv('CC').split()[0].split('gcc')[0]
  elif 'rtems' in traits and traits['rtems']:
    compiler = get_rtems_cc(traits['rtems'])
    rtems_makefile_path = traits['rtems']
    if compiler:
      compiler_prefix = compiler.split()[0].split('gcc')[0]
    else:
      compiler_prefix = ''
  else:
    compiler_prefix = ''
    
  return generator(tree, 
                   prefix = compiler_prefix,
                   root = path,
                   cflags = extra_flags,
                   rtems_makefile_path = rtems_makefile_path)


import dendrite.runner
import yaml
import sys

def main(*argv):
   configuration = yaml.load(open('config/dendrite.yaml'))
   
   return dendrite.runner.start_server(configuration)

if __name__ == "__main__":
   sys.exit(main(sys.argv[1:]))
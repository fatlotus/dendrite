Vagrant::Config.run do |config|
  config.vm.box = "lucid32"
  
  config.vm.provision :shell, :path => 'sbin/setup_environment'
  
  config.vm.forward_port("dendrite", 1337, 1337)
end
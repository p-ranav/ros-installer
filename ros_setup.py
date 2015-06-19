#!/usr/bin/python
# Author: Pranav Srinivas Kumar
# Date: 2015.02.27

import os, sys, subprocess, getopt, pwd, grp

# ROS Indigo Installer class
# 
# Installs ROS Indigo from source at the provided path
# Usage: sudo ./
class ROS_Indigo_Installer():
    # Initialize Installer
    def __init__(self, argv):
        self.path = ""
        self.args = argv
        self.user = ""
        self.sudo_user = ""

        # Print colors
        self.OKGREEN = '\033[92m'
        self.WARNING = '\033[93m'
        self.FAIL = '\033[91m'
        self.ENDC = '\033[0m'
        self.BOLD = '\033[1m'

    # Usage Print
    def usage(self):
        print "INSTALLER::USAGE::\"sudo ./setup_ros.py --path <absolute_path>\""

    # Ensure sudo
    def check_sudo(self):
        self.user = os.getenv("USER")
        self.sudo_user = os.getenv("SUDO_USER")
        if self.user != "root" and self.sudo_user == None:
            print "INSTALLER::Please run this script as root!"
            self.usage()
            sys.exit(2)
        
    # Get absolute path where ROS-Indigo will be setup
    def get_path(self):
        try:
            opts, args = getopt.getopt(self.args, "p:v", ["path="])
        except getopt.GetoptError:
            self.usage()
            sys.exit(2)

        if opts == []:
            self.usage()
            sys.exit(2)
        else:
            for option, value in opts:
                if option == "--path":
                    self.path = value
                else:
                    self.usage()

    # Ask the user a question
    def ask(self, question):

        # Define the valid answers
        valid = {"yes": True, "no": False}
        prompt = " [yes/no] "

        while True:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()
            if choice in valid:
                return valid[choice]
            else:
                print "INSTALLER::Please Respond with a 'yes' or 'no'"

    # Create the ROS Indigo Source Directory
    def create_source_dir(self):
        self.HOME = os.path.join(self.path, "ROS-Indigo")
        print self.WARNING + self.BOLD + "INSTALLER::ROS Installation Path: " + self.HOME + self.ENDC 
        if self.ask("INSTALLER::Proceed with Installation?"):
            if not os.path.exists(self.HOME):
                os.makedirs(self.HOME)
                p = subprocess.Popen('sudo chown -R ' + self.sudo_user + ":" + self.sudo_user + " ./ROS-Indigo",  shell=True)
                p.wait()
                print self.OKGREEN + self.BOLD + "INSTALLER::Created Directory: " + self.HOME + self.ENDC
            else:
                print self.OKGREEN + self.BOLD + "INSTALLER::Found Existing Directory: " + self.HOME + self.ENDC
        else:
            print "INSTALLER::Installation Aborted!"
            sys.exit(2)

    # Setup sources list
    def setup_sources_list(self):
        print "INSTALLER::Setting Up Sources List"
        os.chdir(self.HOME)
        with open("/etc/apt/sources.list.d/ros-latest.list", 
                  "w") as sources:
            sources.write("deb http://packages.ros.org/ros/ubuntu trusty main\n")
            sources.close()
            
    # Setup keys
    def setup_keys(self):
        print "INSTALLER::Setting up Keys"
        os.chdir(self.HOME)
        p1 = subprocess.Popen(["wget", 
                               "https://raw.githubusercontent.com/ros/rosdistro/master/ros.key",
                               '-O', '-'],
                               stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["apt-key", 
                               "add", 
                               "-"], stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()
        output, err = p2.communicate()

    # Apt-get update
    def apt_get_update(self):
        os.chdir(self.HOME)
        p = subprocess.Popen(['apt-get', 'update'])
        p.wait()
        os.system("echo \'" + self.sudo_user + " ALL=(ALL) ALL\'" + " >> /etc/sudoers")

    # Install Bootstrap Dependencies
    def install_bootstrap_dependencies(self):
        print self.OKGREEN + self.BOLD + "INSTALLER::Installing Bootstrap Dependencies" + self.ENDC
        os.chdir(self.HOME)
        p = subprocess.Popen(['apt-get', 
                              'install', 
                              'python-rosdep',
                              'python-rosinstall-generator', 
                              'python-wstool', 
                              'python-rosinstall', 
                              'build-essential'])
        p.wait()

    # Initialize rosdep
    def init_rosdep(self):
        print self.OKGREEN + self.BOLD + "INSTALLER::Initializing rosdep" + self.ENDC
        try:
            os.remove("/etc/ros/rosdep/sources.list.d/20-default.list")
        except OSError:
            pass
        p = subprocess.Popen(['rosdep', 'init'])
        p.wait()
        p = subprocess.Popen(['rosdep', 'fix-permissions'])
        p.wait()
        pw = pwd.getpwnam(self.sudo_user)
        uid = pw.pw_uid
        gid = pw.pw_gid
        with open(os.path.join(self.HOME, "indigo-ros_comm-wet.rosinstall"), 'w') as out:
            out.write("") 
            os.chdir(self.HOME)
            p = subprocess.call(['chown', 
                                 self.sudo_user, 
                                 'indigo-ros_comm-wet.rosinstall'])

            p = subprocess.call(['chgrp', 
                                 self.sudo_user, 
                                 'indigo-ros_comm-wet.rosinstall'])
            p = subprocess.call(['chmod', '-R', '777', self.HOME])

        os.setgid(gid)
        os.setuid(uid)
        os.system("cd " + self.HOME)
        os.system("rosdep update")

    # Install ROS in self.HOME
    def install(self):
        os.chdir(self.HOME)

        print self.OKGREEN + self.BOLD + "INSTALLER::Preparing to fetch core packages" + self.ENDC
        
        # Invoking rosinstall generator
        with open(os.path.join(self.HOME, "indigo-ros_comm-wet.rosinstall"), 'w') as out:
            return_code = subprocess.call(['rosinstall_generator', 
                                           'ros_comm', 
                                           '--rosdistro', 
                                           'indigo', 
                                           '--deps', 
                                           '--wet-only', 
                                           '--tar'], stdout=out)

        print self.OKGREEN + self.BOLD + "INSTALLER::Fetching Core Packages" + self.ENDC
        os.chdir(self.HOME)
        # Invoking wstool on generated .rosinstall file
        p = subprocess.Popen(['wstool', 
                              'init', 
                              '-j8', 
                              'src', 
                              'indigo-ros_comm-wet.rosinstall'])
        p.wait()

        print self.OKGREEN + self.BOLD + "INSTALLER::Resolving Dependencies" + self.ENDC
        
        # Resolving dependencies
        p = subprocess.call(['rosdep', 
                             'install', 
                             '--from-paths', 
                             'src', 
                             '--ignore-src', 
                             '--rosdistro', 
                             '-y'])

        print self.OKGREEN + self.BOLD + "INSTALLER::Building catkin workspace" + self.ENDC

        # Build catkin_workspace!
        p = subprocess.Popen([os.path.join(self.HOME, 'src/catkin/bin/catkin_make_isolated'), 
                              '--install',
                              '-DCMAKE_BUILD_TYPE=Release'])
        p.wait()

    # Add line bashrc
    def addto_bashrc(self):
        command = "echo \"source " + os.path.join(self.HOME, "install_isolated/setup.bash") + "\""  + " >> ~/.bashrc"
        os.system(command)
        print self.OKGREEN + self.BOLD + "INSTALLATION::ROS Indigo - Installation Complete!" + self.ENDC
        

    # Run the installer
    def run(self):
        # Check for sudo
        self.check_sudo()
        # Get absolute path to installation
        self.get_path()
        # Create Directory
        self.create_source_dir()
        # Setup sources list
        self.setup_sources_list()
        # Setup keys
        self.setup_keys()
        # Apt-get update
        self.apt_get_update()
        # Install Bootstrap Dependencies
        self.install_bootstrap_dependencies()
        # Initialize rosdep
        self.init_rosdep()
        # Install ROS
        self.install()
        # Add to bashrc
        self.addto_bashrc()

if __name__ == "__main__":

    # Instantiate a ROS Installer Object
    Installer = ROS_Indigo_Installer(sys.argv[1:])
    # Run the installer
    Installer.run()


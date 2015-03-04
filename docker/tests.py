from manager import Docker

with Docker() as docker:

    docker.run("mkdir builds")
    docker.run("touch builds/readme.txt")
    docker.run("mkdir builds/3")
    docker.run("mkdir builds/4")
    docker.run("touch builds/3/README.txt")
    docker.run("touch builds/3/test.txt")
    docker.run("touch builds/4/test.txt")


    print(docker._list_all_files_and_directories("/builds"))
    print(docker.list_directories("/builds"))
    #print(docker.list_files("/builds"))

import sys

import gitlab
import pkginfo

if __name__ == "__main__":

    if len(sys.argv) != 5:
        print(
            f"usage: {sys.argv[0]} server-url user-token project-id source-file"
        )
        sys.exit(1)

    git_server = sys.argv[1]
    user_token = sys.argv[2]
    project_id = sys.argv[3]
    source_file = sys.argv[4]

    # get the resolved version number, from the source package
    sdist = pkginfo.SDist(source_file)

    gl = gitlab.Gitlab(git_server, user_token)
    proj = gl.projects.get(project_id)

    for p in proj.packages.list():
        if (p.name == sdist.name) and (p.version == sdist.version):
            print(
                f"Removing conflicting registry package `{p.name}@{p.version}' "
                f"(id: {p.id}, files: {len(p.package_files.list())})"
            )
            p.delete()

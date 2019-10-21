#!/usr/bin/env python

import os

import click
import gitlab
import urllib

from . import bdt
from ..release import get_gitlab_instance

from ..log import verbosity_option, get_logger, echo_normal, echo_warning
from ..pipelines import process_log
logger = get_logger(__name__)
from tabulate import tabulate

@click.command(
    epilog="""
Examples:

  1. Process all the jobs from a particular pipeline

     $ bdt gitlab process-pipelines bob/bob.nightlies pipelines

  2. Process a particular job from a pipeline

     $ bdt gitlab process-pipelines bob/bob.nightlies pipelines --job-id xxx

"""
)
@click.argument("package")
@click.argument("pipeline")
@click.option('--job-id', default=None, help='A job id from a pipeline')
@verbosity_option()
@bdt.raise_on_error
def process_pipelines(package, pipeline, job_id):
    """Returns the last tag information on a given PACKAGE."""

    if "/" not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    gl = get_gitlab_instance()

    # we lookup the gitlab package once
    try:
        project = gl.projects.get(package)
        pipeline = project.pipelines.get(pipeline)

        jobs = [j for j in pipeline.jobs.list()]        
        if job_id is not None:
            jobs = [j for j in jobs if int(j.attributes["id"])==int(job_id)]


        if(len(jobs) == 0 ):
            print("Job %s not found in the pipeline %s. Use `bdt gitlab get-pipelines` to search " % (job_id, pipeline.attributes["id"]))
                         
        # Reading log
        try:
            for j in jobs:
                print("Pipeline %s, Job %s" % (pipeline.attributes["id"], int(j.attributes["id"])))
                web_url = j.attributes["web_url"] + "/raw"                
                log = str(urllib.request.urlopen(web_url).read()).split("\\n")
                process_log(log)
        except urllib.error.HTTPError as e:
            logger.warn(
                "Gitlab access error - Log %s can't be found" % web_url, package
            )
            echo_warning("%s: unknown" % (package,))

        logger.info(
            "Found gitlab project %s (id=%d)",
            project.attributes["path_with_namespace"],
            project.id,
        )

        pass
    except gitlab.GitlabGetError as e:
        logger.warn("Gitlab access error - package %s does not exist?", package)
        echo_warning("%s: unknown" % (package,))


@click.command(
    epilog="""
Examples:

  1. Get the most recent pipelines from a particular project wit their corresponding job numbers

     $ bdt gitlab get-pipelines bob/bob.nightlies


"""
)
@click.argument("package")
@verbosity_option()
@bdt.raise_on_error
def get_pipelines(package):
    """Returns the CI pipelines given a given PACKAGE."""

    if "/" not in package:
        raise RuntimeError('PACKAGE should be specified as "group/name"')

    gl = get_gitlab_instance()

    # we lookup the gitlab package once
    try:
        project = gl.projects.get(package)
        logger.info(
            "Found gitlab project %s (id=%d)",
            project.attributes["path_with_namespace"],
            project.id,
        )

        pipelines = project.pipelines.list()
        description = [["Pipeline", "Branch", "Status", "Jobs"]]
        for pipeline in pipelines:
            jobs = [j.attributes["id"] for j in pipeline.jobs.list()]
            description.append(
                [
                    "%s" % pipeline.attributes["id"],
                    "%s" % pipeline.attributes["ref"],
                    "%s" % pipeline.attributes["status"],
                    "%s" % jobs,
                ]
            )
        print("Jobs from project %s" % package)
        print(tabulate(description))

    except gitlab.GitlabGetError as e:
        logger.warn("Gitlab access error - package %s does not exist?", package)
        echo_warning("%s: unknown" % (package,))

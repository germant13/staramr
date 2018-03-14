import logging
import subprocess
import time
from os import path

import git

from staramr.blast.pointfinder.PointfinderBlastDatabase import PointfinderBlastDatabase
from staramr.blast.resfinder.ResfinderBlastDatabase import ResfinderBlastDatabase

logger = logging.getLogger('AMRDatabaseHandler')

"""
A Class used to handle interactions with the ResFinder/PointFinder database files.
"""


class AMRDatabaseHandler:

    def __init__(self, database_dir):
        """
        Creates a new AMRDatabaseHandler.
        :param database_dir: The root directory for both the ResFinder/PointFinder databases.
        """
        self._database_dir = database_dir
        self._resfinder_dir = path.join(database_dir, 'resfinder')
        self._pointfinder_dir = path.join(database_dir, 'pointfinder')

        self._resfinder_url = "https://bitbucket.org/genomicepidemiology/resfinder_db.git"
        self._pointfinder_url = "https://bitbucket.org/genomicepidemiology/pointfinder_db.git"

    @classmethod
    def get_default_database_directory(cls, script_dir):
        """
        Class method for getting the default database root directory.
        :param script_dir: The directory containing the main application script.
        :return: The default database root directory.
        """
        return path.join(script_dir, 'databases')

    @classmethod
    def create_default_handler(cls, script_dir):
        """
        Class method for getting the default database handler.
        :param script_dir: The directory containing the main application script.
        :return: The default database handler.
        """
        return cls(cls.get_default_database_directory(script_dir))

    def build(self):
        """
        Downloads and builds a new ResFinder/PointFinder database.
        :return: None
        """
        logger.info("Cloning resfinder db [" + self._resfinder_url + "] to [" + self._resfinder_dir + "]")
        git.repo.base.Repo.clone_from(self._resfinder_url, self._resfinder_dir)

        logger.info("Cloning pointfinder db [" + self._pointfinder_url + "] to [" + self._pointfinder_dir + "]")
        git.repo.base.Repo.clone_from(self._pointfinder_url, self._pointfinder_dir)

        self._blast_format()

    def update(self):
        """
        Updates an existing ResFinder/PointFinder database to the latest revisions.
        :return: None
        """
        resfinder_repo = git.Repo(self._resfinder_dir)
        pointfinder_repo = git.Repo(self._pointfinder_dir)

        logger.info("Updating " + self._resfinder_dir)
        resfinder_repo.heads.master.checkout()
        resfinder_repo.remotes.origin.pull()

        logger.info("Updating " + self._pointfinder_dir)
        pointfinder_repo.heads.master.checkout()
        pointfinder_repo.remotes.origin.pull()

        self._blast_format()

    def info(self):
        """
        Prints out information on the ResFinder/PointFinder databases.
        :return: None
        """
        data = []

        resfinder_repo = git.Repo(self._resfinder_dir)
        resfinder_repo_head = resfinder_repo.commit('HEAD')

        data.append(['resfinder_db_dir', self._resfinder_dir])
        data.append(['resfinder_db_commit', str(resfinder_repo_head)])
        data.append(
            ['resfinder_db_date', time.strftime("%a, %d %b %Y %H:%M", time.gmtime(resfinder_repo_head.committed_date))])

        pointfinder_repo = git.Repo(self._pointfinder_dir)
        pointfinder_repo_head = pointfinder_repo.commit('HEAD')
        data.append(['pointfinder_db_dir', self._pointfinder_dir])
        data.append(['pointfinder_db_commit', str(pointfinder_repo_head)])
        data.append(['pointfinder_db_date',
                     time.strftime("%a, %d %b %Y %H:%M", time.gmtime(pointfinder_repo_head.committed_date))])

        self._print_data(data)

    def _print_data(self, data):
        max_width = max([len(w[0]) for w in data])

        for item in data:
            print(item[0].ljust(max_width) + " = " + item[1])

    def _blast_format(self):

        logger.info("Formatting resfinder db")
        resfinder_db = ResfinderBlastDatabase(self._resfinder_dir)
        for path in resfinder_db.get_database_paths():
            self._make_blast_db(path)

        logger.info("Formatting pointfinder db")
        for organism_db in PointfinderBlastDatabase.build_databases(self._pointfinder_dir):
            for path in organism_db.get_database_paths():
                self._make_blast_db(path)

    def _make_blast_db(self, path):
        command = ['makeblastdb', '-in', path, '-dbtype', 'nucl', '-parse_seqids']
        logger.debug(' '.join(command))
        subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE).check_returncode()
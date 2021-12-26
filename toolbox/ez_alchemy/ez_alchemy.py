"""
Functions for Interfacing with databases at PJM using SQLAlchemy
"""
import os
import pandas as pd
from sqlalchemy import engine, __version__ as alch_ver
# from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from toolbox.simple_password import get_credentials
# from toolbox import toolbox_config, pjm_config
from toolbox import tb_cfg
from typing import Union
from collections import deque, namedtuple
from contextlib import contextmanager
import warnings
try:
    import cx_Oracle
except Exception as e:
    warnings.warn("Failed to import cx-Oracle.  " 
                  "See https://cx-oracle.readthedocs.io/en/latest/user_guide/installation.html")

alch_ver = [int(s) for s in alch_ver.split('.')]
default_user = os.environ['username']

NoneType = type(None)
cfg = tb_cfg
default_dialect = cfg['ORACLE']['DIALECT']
default_sql_driver = cfg['ORACLE']['DRIVER']
default_hosts = tb_cfg["DEFAULT_HOSTS"]
CredsTuple = namedtuple('CredsTuple', ['hosts', 'user', 'pw'])
global_creds = CredsTuple(tb_cfg["DEFAULT_HOSTS"], '', '')

def ez_query(sql, host:str = global_creds.hosts, user:str = global_creds.user,
             pw:str = global_creds.pw, as_dataframe:bool = True):
    global global_creds
    result = EZOracle(hosts=host, user = user, pw = pw,
                    sql = sql, as_dataframe = as_dataframe).result
    # If db connected, then save the credentials to global_creds
    global_creds = CredsTuple(host, user, pw)
    return result
    # with EZOracle() as db:
    #     result = EZOracle(hosts=host, user = user, pw = pw,
    #                       sql = sql, as_dataframe = as_dataframe).result
    # return result

class EZDB:
    """
    You can use this class directly, however it is intended as an abstract
    class to be inherited by EZOracle or other custom classes.
    """
    def __init__(self, hosts:Union[list, tuple, set, str] = default_hosts,
                 user:str = '',
                 pw:str = '',
                 sql:str = None,
                 login_on_instantiate:bool = True,
                 as_dataframe = True,
                 auto_commit = False,
                 dialect = None,
                 sql_driver = None,
                 *engine_args,
                 **engine_kwargs):
        """
        EZOracle is a SQLAlchemy wrapper for PJM databases.  It creates an
        SQLAlchemy engine, logs in, and executes SQL.  Wrapping in a with
        statement allows a user to connect to the db, execute a command and
        return the result like:
            host, user, pw = get_credentials(system='EXSCTSTG')
            with db as EZOracle(hosts=host, user=user, pw=pw)
                result = db.execute(sql = "select sysdate from dual")
        :param hosts: name of host or list-like of hosts.  If list-like is
                      provided, then the get_credentials dialogue is displayed.
        :param user: if not provided, then the get_credentials dialogue is
                         displayed and OS user the default value.
        :param pw: if not provided, then the get_credentials dialogue is
                         displayed.
        :param sql: sql statement to execute
        :param login_on_instantiate: True/False
                                     True:  attempt to login to db when this
                                            class is instantiated
                                     False: do not attempt to login on
                                            instantiation.
        :param as_dataframe: True/False
                                    True:  .result property returns a Pandas DataFrame
                                    False: .result property returns a dict-like object
        :param auto_commit: True/False
                            True:  prior exit/destroy, executed slq statements
                                  are committed to db.
                            False: prior to exit/destroy, uncommitted sql
                                   statements are rolled back.
        """
        self._host = ''
        # read arguments
        self._hosts = []  # this line is not needed
        self.hosts = hosts
        self.user:str = user.strip()
        self._pw:str = pw.strip()
        self._sql:str = ''
        self.sql:str = sql
        self.login_on_instantiate:bool = login_on_instantiate
        self.result_as_DataFrame:bool = as_dataframe
        self.auto_commit:bool = auto_commit
        self.engine_args = engine_args
        self.engine_kwargs = engine_kwargs
        if 'host' in engine_kwargs:
            raise ValueError(f"'host' is an invalid argument.  Did you mean 'hosts{self.host}'?")

        # set properties
        if len(self.hosts) == 1:
            self.host = self.hosts
        self._dialect = dialect
        self.sql_driver = sql_driver
        self._result = None
        self._session = None
        self._engine = None
        self._execution_history = deque(maxlen=50)

        if login_on_instantiate:
            self.create_engine()
            if self.sql:
                self.execute()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            if self.auto_commit:
                self._session.commit()
            else:
                self._session.rollback()
            self._session.close()

        if self._engine:
            self._engine.dispose()
            del self._engine

    @property
    def dialect(self):
        return self._dialect

    @dialect.setter
    def dialect(self, new_dialect:str):
        if self._engine:
            raise SyntaxError('Cannot change dialect once engine created.')
        else:
            self._dialect = new_dialect

    @property
    def sql(self):
        return self._sql

    @sql.setter
    def sql(self, new_sql: str):
        if new_sql:
            self._sql = new_sql.strip().rstrip (';')
        else:
            self._sql = ''

    @property
    def pw(self):
        return len(self._pw) * '*'

    @pw.setter
    def pw(self, new_pw):
        self._pw = new_pw.strip()

    @property
    def hosts(self):
        if type(self._hosts) == str:
            self._hosts = [self._hosts]
        elif not self._hosts:
            self._hosts = []
        return self._hosts

    @hosts.setter
    def hosts(self, new_hosts:Union[list, tuple, set, str]):
        """List of hosts to display in login window. """
        assert type(new_hosts) in [list, tuple, set, str]
        # convert new_hosts to a unique set
        if type(new_hosts) == str:
            new_hosts = [new_hosts]
        # remove zero length host names from _hosts
        self._hosts = [host.strip () for host in new_hosts
                           if len(new_hosts) > 0]

    @property
    def result(self):
        return self._result

    @property
    def host(self):
        """ Return the host (database name)"""
        if not self._host:
            if type(self._hosts) == str:
                self._host = self._hosts
            elif len(self.hosts) == 1:
                if type(self.hosts[0]) == str:
                    self._host = self._hosts[0]
        return self._host

    @host.setter
    def host(self, new_host):
        """
        Set a new host (database name).
        :param new_host: str or list-like object containing exactly 1 str
        """
        if type(new_host) == str:
            self._host = new_host
        else:
            msg = 'host expected a str or list-like of 1 values; ' +  \
                  f'received {len(new_host)}'
            assert len(new_host) == 1, msg
            msg = 'host expected a str or list-like of 1 values; ' +  \
                  f'received list of type {type(new_host[0]).__name__}'
            assert type (new_host[0]) == str, msg
            self._host = new_host[0]

    def create_engine(self):
        if self._engine:
            raise PermissionError('Engine already created.')
        elif not self._dialect:
            raise SyntaxError ('Dialect not set.')
        elif not self.sql_driver:
            raise SyntaxError('SQL Driver not set')

        if len (self._hosts) == 1:
            self.host = self._hosts[0]

        if not self.host or not self.user or not self._pw:
            self.user = self.user or default_user
            creds = get_credentials (window_title = 'DB Login',
                                     systems = self._hosts,
                                     user = self.user,
                                     pw = self._pw)
            self._hosts = creds.system.strip ()
            self.user = creds.user.strip ()
            self._pw = creds.pw.strip ()

        if self.host and self.user and self._pw:
            # build connection string
            engine_path_win_auth = self._dialect + '+' + self.sql_driver + '://' \
                                   + self.user + ':' + self._pw \
                                   + '@' + self.host
            # add connection string to arguments to pass to SQLAlchemy
            args = tuple([engine_path_win_auth]
                         + list(self.engine_args))
            # Call SQLAlchemy's create_engine function.  #Does NOT verify credentials or host

            self._engine = engine.create_engine(*args,
                                                **self.engine_kwargs)
        else:
            raise ConnectionError

        return self._engine

    def _create_session(self):
        if not self._engine:
            self.create_engine()
        if self._engine:
            self._session = sessionmaker(bind = self._engine)
        return self._session

    @staticmethod
    def _ora_error_type(ora_error_code: str):
        """
        This is a helper function to help determine what to do when certain oracle errors are
        received.
        :param ora_error_code:
        :return: 0: unclassified error
                 1: can't login
                 2: serious error
                 3: bad query (error in SQL statement)
        """
        id_pw = {'01017': 'ORA-01017: invalid username/password; logon denied'}
        cant_connect = {'12154': 'ORA-12154: TNS:could not resolve the connect identifier '
                                 'specified',
                      '3113': 'ORA-03113: end-of-file on communication channel',
                      '12514': 'TNS:listener does not currently know of service requested in connect descriptor'
                      }
        serious_err = {'00600': 'ORA-00600: internal error code, arguments: [%s], [%s],[%s], [%s], [%s]',
                       '01000': 'ORA-01000: maximum open cursors exceeded',
                       '12560': '12560',
                       '06512': 'at stringline string',
                       '12505': 'TNS:listener does not currently know of SID given in connect descriptor'
                       }
        bad_query = {'1722': 'ORA-1722: Invalid Number',
                     '00942': 'ORA-00942: table or view does not exist'
                     }

        if any(s in ora_error_code for s in id_pw.keys()):
            return 1  # can't login
        elif any(s in ora_error_code for s in serious_err.keys()):
            return 2  # serious error
        elif any(s in ora_error_code for s in bad_query.keys()):
            return 3  # bad query (bad SQL)
        elif any(s in ora_error_code for s in cant_connect.keys()):
            return 4  # can't connect to db
        else:
            return 0  # error not yet classified

    def execute(self, sql:str = None):
        self._result = None
        self.sql = sql or self.sql
        self.sql = self.sql.strip().rstrip(';')
        assert len(self.sql)>0, 'sql statement is missing or empty'
        if self._engine and self.sql:
            attempts = 1
            while attempts <= 3:
                if not self.host or not self.user or not self._pw:
                    self.create_engine()
                try:
                    if self.result_as_DataFrame:
                        self._result = pd.read_sql_query(self.sql, self._engine)
                    else:
                        # engine.Engine.execute(self.sql)
                        self._result = self._engine.execute(self.sql)
                        if self.auto_commit:
                            self._engine.execute('commit')
                    self._execution_history.append(self.sql)
                    attempts = 10
                except cx_Oracle.DatabaseError as e:
                    print(f'Oracle error executing SQL statement "{self._sql}".')
                    print(e)
                    attempts += 1
                    if self._engine:
                        self._engine.dispose()
                        self._engine = None
                        # self.user = ''
                    self._pw = ''
                except Exception as e:
                    attempts += 1
                    err_txt = str(e)
                    err_type = self._ora_error_type(err_txt)
                    print(f'Oracle error executing SQL statement "{self._sql}".')
                    print(err_txt)
                    if err_type == 0:
                        raise
                    elif err_type == 1:
                        # id/pw error
                        pass
                    elif err_type == 2:
                        # serious error
                        raise
                    elif err_type == 3:
                        # bad query (error in SQL statement)
                        raise
                    elif err_type == 4:
                        # can't connect to db
                        raise
                    else:
                        # uncategorized error.
                        # consider adding error code in self._ora_error_type
                        raise
                    if self._engine:
                        self._engine.dispose()
                        self._engine = None
                        # self.user = ''
                    self._pw = ''
            if attempts == 4:
                print(f'*** Failed to login to {str(self.host)} 3 times. *** ')
        return self._result

    def query(self, sql:str = None):
        """ Alias for self.execute """
        return self.execute(sql)
    q = query

    def itertuples(self, index=False, name=None):
        if isinstance(self._result, pd.DataFrame):
            return self._result.itertuples(index=index, name=name)
        else:
            # TODO: not sure if this will convert the dict to a pd.DataFrame
            # as expected, where each key represents a column.
            # df = pd.DataFrame(self._result.items(), columns=self._result.keys())
            df = pd.DataFrame(self._result)
            return df.itertuples()

    def iteritems(self):
        return self._result.iteritems()

    def iterrows(self):
        return self._result.iterrows()

    @contextmanager
    def atomic(self):
        """Run queries as atomic transactions.  Context manager.
        Usage at console:
            $ db = EZOracle('db', 'id', 'pw')
            $ with db.atomic():
            $     db.execute("insert into db.tbl1 values ('a','b','c')")
            $     db.execute("insert into db.tbl1 values ('d','e','f')")
            $     raise Exception("Oh no, something bad happened!!")
            $     db.execute("insert into db.tbl1 values ('g','h','i')")

            When inside the atomic context, none of the values will
            be inserted if an exception occurs.
        """
        try:
            self._session.begin()
            yield
        except:
            # Rollback!
            self._session.rollback()
            print("*** ROLLBACK ***")
            raise
        else:
            self._session.commit()


# class EZOracle(EZDB):
#     def __init__(self, hosts:Union[list, tuple, set, str] = default_hosts,
#                  user:str = '',
#                  pw:str = '',
#                  sql:str = None,
#                  login_on_instantiate:bool = True,
#                  as_dataframe = True,
#                  auto_commit = False,
#                  *engine_args,
#                  **engine_kwargs):
#
#         super().__init__(hosts = hosts,
#                          user = user,
#                          pw = pw,
#                          sql = sql,
#                          as_dataframe = as_dataframe,
#                          auto_commit = auto_commit,
#                          dialect = cfg['ORACLE']['DIALECT'],
#                          sql_driver = cfg['ORACLE']['DRIVER'],
#                          *engine_args,
#                          **engine_kwargs)

class EZOracle(EZDB):
    def __init__(self, hosts:Union[list, tuple, set, str] = default_hosts,
                 user:str = '',
                 pw:str = '',
                 sql:str = None,
                 login_on_instantiate:bool = True,
                 as_dataframe = True,
                 auto_commit = False,
                 # max_identifier_length: int = 128,
                 *engine_args,
                 **engine_kwargs):

        # This if...else statement added in version 2021.08.6
        # https://gerrit.sqlalchemy.org/c/sqlalchemy/sqlalchemy/+/1489/
        # https://docs.sqlalchemy.org/en/14/dialects/oracle.html#max-identifier-lengthsimp
        if alch_ver[0] == 1 and alch_ver[1] < 4:
            engine_kwargs.setdefault('max_identifier_length', 128)

        super().__init__(hosts = hosts,
                         user = user,
                         pw = pw,
                         sql = sql,
                         as_dataframe = as_dataframe,
                         auto_commit = auto_commit,
                         dialect = cfg['ORACLE']['DIALECT'],
                         sql_driver = cfg['ORACLE']['DRIVER'],
                         *engine_args,
                         **engine_kwargs)

# _oracle_db = EZOracle()

class _Examples:
    """
    Contains example use of the EZOracle class and it's ez_query wrapper
    function.  You can actually execute any of these modules either at the
    Python Console, for example:

        $ from ez_alchemy import _Examples
        $ _Examples.ez_query_one_line()

    You can also edit the main() function in this module to run any of the
    examples in this class.  For example:

        def main():
        _Examples.sqlalchemy_oracle_example()
    """
    @classmethod
    def sqlalchemy_oracle_example(cls):
        dialect, sql_driver = 'oracle', 'cx_oracle'
        hosts = default_hosts
        host, usr, pwd = get_credentials(systems = hosts)
        engine_string = dialect + '+' + sql_driver + '://' + usr + ':' + pwd +'@' + host
        db = engine.create_engine(engine_string)
        sql = "select * from all_tab_columns where ROWNUM <=10 order by table_name"
        df = pd.read_sql_query(sql, db)
        print(df.columns)
        print(df)

    @classmethod
    def ez_query_one_line(cls):
        # If not provided, ez_query prompts for user and pw
        df = ez_query(sql = "select sysdate from dual", host= 'EXSCRSTG')
        print(df)

    @classmethod
    def ez_query_with_creds(cls):
        # You can choose to collect credentials independently and use them
        # repeatedly for multiple quick queries.
        host, usr, pw = get_credentials("ez_query_ex1",
                                        systems = tb_cfg["DEFAULT_HOSTS"])
        df = ez_query(sql = "select sysdate from dual", host = host,
                      user = usr, pw = pw)
        print(df)
        df = ez_query(sql = "select sysdate from dual", host = host,
                      user = usr, pw = pw)
        print(df)

    @classmethod
    def ez_oracle_no_context_mgmt(cls):
        """
        In this example, we keep our connection pool open, so we need to
        clean it up with a simple "del" statement
        """
        db = EZOracle(sql = "select sysdate from dual")
        df = db.result
        del db
        print(df)

    @classmethod
    def ez_oracle_in_with_statement(cls):
        """
        Using a "with" statement as a context manager, run 2 sql statements
        in a single connection pool.
        """
        with EZOracle() as db:
            result = db.execute(sql = "select 1, sysdate from dual")
            result2 = db.execute(sql = "select 2, sysdate from dual")
        print(result2)

    @classmethod
    def ez_oracle_with_bad_creds(cls):
        """
        When bad credentials are encountered, the first login will
        fail behind the scenes, then the user will be prompted for
        credentials via dialog box.
        """
        sql = "select sysdate from dual"
        with EZOracle(hosts = 'EXSCRSTG',
                      user = 'fake_user',
                      pw = 'some_password') as db:
            # The following should fail, because bad credentials are used.
            try:
                result = db.execute(sql = sql).result
                print (result)
            except AttributeError as e:
                print('Unable to query database. ', e)

    @classmethod
    def ez_oracle_with_bad_sql(cls):
        """
        Using a "with" statement as a context manager, run 2 sql statements
        in a single connection pool.
        """
        with EZOracle() as db:
            # print('\nExecuting good query...')
            # result = db.execute(sql = "select sysdate from dual")
            # print(result)
            print('\nExecuting bad query...')
            result2 = db.execute(sql = "select * from fake_table")
            print(result2)


def main():
    # _Examples.sqlalchemy_oracle_example()
    #  _Examples.ez_query_one_line()
    # _Examples.ez_query_with_creds()
    # _Examples.ez_oracle_no_context_mgmt()
    # _Examples.ez_oracle_in_with_statement()
    _Examples.ez_oracle_with_bad_creds()
    #_Examples.ez_oracle_with_bad_sql()

if __name__ == '__main__':
    main()

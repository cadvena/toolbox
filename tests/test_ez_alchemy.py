import os
import unittest
from toolbox.ez_alchemy import EZOracle, ez_query, _Examples
import pandas as pd
from sqlalchemy import engine
from toolbox.simple_password import get_credentials
from toolbox import tb_cfg

DEFAULT_USER = os.environ['username']

NoneType = type (None)
cfg = tb_cfg


class TestEZQuery(unittest.TestCase):
    def setUp(self):
        print("\nCalling TestOSWrapper.setUp()...")
        self.hosts = tb_cfg['DEFAULT_HOSTS']
        self.host, self.usr, self.pw = get_credentials(systems = self.hosts)
        self.sql = 'select sysdate from dual'
        # verify we can run a simple query before we run remaining tests
        ez_query(sql=self.sql, host=self.host, user=self.usr, pw=self.pw)

    def tearDown(self):
        print("\nCalling TestOSWrapper.tearDown()...")

    def test_sqlalchemy_oracle_example(self):
        expexted_cols = ["OWNER", "TABLE_NAME", "COLUMN_NAME", "DATA_TYPE", "DATA_TYPE_MOD",
                         "DATA_TYPE_OWNER", "DATA_LENGTH", "DATA_PRECISION", "DATA_SCALE",
                         "NULLABLE", "COLUMN_ID", "DEFAULT_LENGTH", "DATA_DEFAULT", "NUM_DISTINCT",
                         "LOW_VALUE", "HIGH_VALUE", "DENSITY", "NUM_NULLS", "NUM_BUCKETS",
                         "LAST_ANALYZED", "SAMPLE_SIZE", "CHARACTER_SET_NAME",
                         "CHAR_COL_DECL_LENGTH", "GLOBAL_STATS", "USER_STATS", "AVG_COL_LEN",
                         "CHAR_LENGTH", "CHAR_USED", "V80_FMT_IMAGE", "DATA_UPGRADED", "HISTOGRAM",
                         "DEFAULT_ON_NULL", "IDENTITY_COLUMN", "EVALUATION_EDITION",
                         "UNUSABLE_BEFORE", "UNUSABLE_BEGINNING", "COLLATION"]
        dialect, sql_driver = 'oracle', 'cx_oracle'

        engine_string = dialect + '+' + sql_driver + '://' + self.usr + ':' + self.pw + '@' + self.host
        db = engine.create_engine (engine_string)
        sql = "select * from all_tab_columns where ROWNUM <=10 order by table_name"
        df = pd.read_sql_query (sql, db)
        self.assertEqual (10, df.shape[0])
        cols = [s.lower () for s in list (df.columns)]
        expected_cols = [s.lower () for s in expexted_cols]
        self.assertEqual (expected_cols, cols)
        print (df)

    def test_ez_query_one_line(self):
        # def ez_query(sql, host: str = default_hosts, user: str = '', pw: str = '',
        #              as_dataframe = True):
        # If not provided, ez_query prompts for user and pw
        df = ez_query(sql = "select sysdate from dual", host= self.host, user= self.usr,
                      pw = self.pw)
        self.assertTrue(df.shape, (1,1))

    def test_ez_query_with_creds(self):
        # You can choose to collect credentials independently and use them
        # repeatedly for multiple quick queries.
        df = ez_query(sql = "select sysdate from dual", host = self.host,
                      user = self.usr, pw = self.pw)
        self.assertTrue (df.shape, (1, 1))
        df = ez_query(sql = "select sysdate from dual", host = self.host,
                      user = self.usr, pw = self.pw)

class TestEZOracle(unittest.TestCase):
    def setUp(self):
        print ("\nCalling TestOSWrapper.setUp()...")
        self.hosts = tb_cfg['DEFAULT_HOSTS']
        self.host, self.usr, self.pw = get_credentials (systems = ['EXSCRSTG'])
        self.sql = 'select sysdate from dual'
        # verify we can run a simple query before we run remaining tests
        ez_query (sql = self.sql, host = self.host, user = self.usr, pw = self.pw)

    def tearDown(self):
        print ("\nCalling TestOSWrapper.tearDown()...")

    def test_ez_oracle_one_line(self):
        """
        Run a single query without worrying about cleaning up.
        EZOracle cleans itself up.
        """
        df = EZOracle(sql = "select sysdate from dual", hosts = self.host,
                      user = self.usr, pw = self.pw).result
        print (df)

    def test_ez_oracle_no_context_mgmt(self):
        """
        In this example, we keep our connection pool open, so we need to
        clean it up with a simple "del" statement
        """
        db = EZOracle(sql = "select sysdate from dual", hosts = self.host,
                      user = self.usr, pw = self.pw)
        df = db.result
        del db
        print(df)

    def test_ez_oracle_in_with_statement(self):
        """
        Using a "with" statement as a context manager, run 2 sql statements
        in a single connection pool.
        """
        with EZOracle(hosts = self.host, user = self.usr, pw = self.pw) as db:
            result = db.execute(sql = "select 1, sysdate from dual")
            result2 = db.execute(sql = "select 2, sysdate from dual")
        print(result)
        print(result2)

    def test_ez_oracle_with_bad_creds(self):
        """
        When bad credentials are encountered, the first login will
        fail behind the scenes, then the user will be prompted for
        credentials via dialog box.
        """
        sql = "select sysdate from dual"
        # host, user, pw = get_credentials()
        with EZOracle(hosts = self.host,
                      user = 'fake_user',
                      pw = 'some_password') as db:
            db.execute (sql = sql)

        pass


if __name__ == '__main__':
    ### 2 - invoke the framework ###
    # invoke the unittest framework
    # unittest.main() will capture all fo the tests
    # and run them 1-by-1.
    unittest.main ()
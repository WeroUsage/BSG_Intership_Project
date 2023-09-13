#%%
def extract_table(query_name):
    import sys
    sys.path.append("..")
    from utils.db_connection import DBConnection
    from utils.db_query_utils import DBQuery

    db_handler = DBConnection(config_file = "db.conf.sample",root_folder=r"C:\Users\a.tsereteli\Silknet_Cases\Case_11")
    cursor = db_handler.get_cursor()
    root = r"C:\Users\a.tsereteli\Silknet_Cases\Case_11"
    test_query = DBQuery(file_name=query_name, cursor=cursor, by_steps=False, base_folder="queries", root_folder=root)
    return test_query.run()




#%%

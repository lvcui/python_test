# manage为主文件 主要执行该文件
from flask import current_app

from info import create_app,db
from flask_script import Manager
from flask_migrate import Migrate,MigrateCommand


app = create_app("development")
manager = Manager(app)
Migrate(app,db)
manager.add_command('db',MigrateCommand)



if __name__ == '__main__':

    manager.run()
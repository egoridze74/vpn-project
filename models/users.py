from models.dbo import DBO

class Users(DBO):
    def __init__(self, db, ID=None):
        fields = [
            "ID",
            "Username",
            "Password",
            "HashType",
            "UserRoleID",
            "Author",
            "Created_date",
            "Last_editor",
            "Last_change",
            "Change_cnt",
        ]

        super().__init__(db, table_name="Users", fields=fields, pk="ID")

        if ID is not None:
            self.load(ID)
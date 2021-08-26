# -*- coding: utf-8 -*-


class UserIdentifier:
    """ Класс информации о пользователе
    """

    def __init__(self, user_info):
        """ Конструктор
        
        :param user_info: dict() - configuration.USER_DB_FIELDS
        """
        self.user_info = user_info

    def get_fio(self):
        if "fio" in self.user_info:
            return self.user_info["fio"]
        return u""

    def get_user_id(self):
        if "db_user_id" in self.user_info:
            return self.user_info["db_user_id"]
        return u""

    def is_admin(self):
        if "admin" in self.user_info:
            return self.user_info["admin"]
        return 0

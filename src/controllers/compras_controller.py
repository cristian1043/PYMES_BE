from src.models.compras import Compras


class ComprasController:

    @staticmethod
    def get():
        return session.query(Compras).all()


    @staticmethod
    def get_by_id(id):
        return session.query(Compras).filter_by(id=id).first()


    @staticmethod
    def save(compra):

        try:
            session.add(compra)
            session.commit()
            return compra

        except SQLAlchemyError:
            session.rollback()
            return None


    @staticmethod
    def update(compra):

        if compra is None:
            return False

        try:
            session.commit()
            return True

        except SQLAlchemyError:
            session.rollback()
            return False


    @staticmethod
    def delete(compra):

        if compra is None:
            return False

        try:
            session.delete(compra)
            session.commit()
            return True

        except SQLAlchemyError:
            session.rollback()
            return False
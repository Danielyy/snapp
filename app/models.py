from . import db


class SeriesNumber(db.Model):
    __tablename__ = 'series_numbers'
    id = db.Column(db.Integer, primary_key=True)
    series_number = db.Column(db.Integer, unique=True)
    category = db.Column(db.String(20))
    sn_input_date = db.Column(db.DateTime)
    sn_output_date = db.Column(db.DateTime)
    user_account = db.Column(db.String(256))
    receipt_status = db.Column(db.Boolean)

    def __init__(self, series_number, category, sn_input_date, sn_output_date, user_account, receipt_status):
        self.series_number = series_number
        self.category = category
        self.sn_input_date = sn_input_date
        self.sn_output_date = sn_output_date
        self.user_account = user_account
        self.receipt_status = receipt_status

    def __repr__(self):
        return '<SeriesNumber {}>'.format(self.series_number)
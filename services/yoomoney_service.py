from yoomoney import Client, Quickpay
from config import YOOMONEY_PROVIDER_TOKEN, YOOMONEY_CLIENT_CARDID
import uuid

class YooMoney:
    def __init__(self):
        self.client = Client(YOOMONEY_PROVIDER_TOKEN)

    def create_quickpay(self, amount: int, target: str = "AutoBay"):
        uuid_tx = str(uuid.uuid4())
        quickpay = Quickpay(
            receiver=str(YOOMONEY_CLIENT_CARDID),
            quickpay_form="shop",
            targets=target,
            paymentType="SB",
            sum=amount,
            label=uuid_tx
        )
        return quickpay.base_url, uuid_tx

    # def check_tx(self, uuid_tx: str):
    #     history = self.client.operation_history(label=uuid_tx)
    #     for op in history.operations:
    #         if op.label == uuid_tx:
    #             if op.status == 'success':
    #                 return True, op.operation_id
    #             return False, None
    #     return False, None

    # MOCK
    def check_tx(self, uuid_tx: str):
        history = self.client.operation_history(label=uuid_tx)
        for op in history.operations:
            if op.label == uuid_tx:
                if op.status == 'success':
                    return True, op.operation_id
                return True, True
        return True, True
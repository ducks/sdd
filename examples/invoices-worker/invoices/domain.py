"""Existing synchronous invoice formatter; money is integer cents."""
def render_invoice(invoice):
    if invoice.get('currency') not in ('USD', 'EUR', 'CZK'):
        raise ValueError('unsupported currency')
    lines = invoice['lines']
    if not lines or any(type(line['cents']) is not int or line['cents'] < 0 for line in lines):
        raise ValueError('invalid invoice lines')
    return {'invoice': invoice['id'], 'currency': invoice['currency'],
            'total_cents': sum(line['cents'] for line in lines)}

from django.shortcuts import render, get_object_or_404
from models import Item, Bill, BillItem, ShopUser, Customer
from forms import ItemForm, BillForm, BillItemForm
from django.contrib.auth.decorators import login_required


@login_required
def get_shop(request):
    """
    Tries to get the shop associated to an account
    """
    try:
        user = request.user
        shopuser = ShopUser.objects.get(user=user)
        return shopuser.shop
    except ShopUser.DoesNotExist:
        raise Exception("Access Denied, you have access to no shops")


@login_required
def index(request):
    items = Item.objects.filter(shop=get_shop(request))
    bills = Bill.objects.filter(shop=get_shop(request))
    param_dict = {
        'items': items,
        'bills': bills,
    }
    return render(request, "billing/index.html", param_dict)


@login_required
def view_item(request, item_id):
    param_dict = {
        'item': get_object_or_404(Item, pk=item_id, shop=get_shop(request)),
    }
    return render(request, "billing/view_item.html", param_dict)


@login_required
def edit_item(request, item_id):
    item = get_object_or_404(Item, pk=item_id, shop=get_shop(request))
    if request.method == 'POST':
        form = ItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save(commit=True)
            return view_item(request, item_id)
        else:
            print form.errors
    else:
        form = ItemForm(instance=item)
    return render(request, "billing/edit_item.html", {'form': form, 'item_id': item_id})


@login_required
def view_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id)
    param_dict = {
        'bill': bill,
    }
    return render(request, "billing/view_bill.html", param_dict)


@login_required
def new_bill(request):
    customer, created = Customer.objects.get_or_create(name='Consumidor Final')
    new = Bill(shop=get_shop(request), issued_to=customer)
    new.save()
    return view_bill(request, new.pk)


@login_required
def edit_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
    if not bill.can_be_modified():
        # The bill has been issued, and can't be modified
        raise Exception("The bill can't be modified")

    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save(commit=True)
            return view_bill(request, bill_id)
        else:
            print form.errors
    else:
        form = BillForm(instance=bill)
    return render(request, "billing/edit_bill.html", {'form': form, 'bill_id': bill_id})

    items = BillItem.objects.filter(bill=bill)
    param_dict = {
        'bill': bill,
        'items': items,
    }
    return render(request, "billing/view_bill.html", param_dict)

@login_required
def delete_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
    if request.method == 'POST':
        if bill.is_proforma:
            items = BillItem.objects.find(bill=bill)
            for item in items:
                item.delete()
            bill.delete()
        else:
            raise Exception("Bill is definitive")
    return index(request)

@login_required
def add_item_to_bill(request, bill_id):
    bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
    if not bill.can_be_modified():
        # The bill has been issued, and can't be modified
        raise Exception("The bill can't be modified")

    if request.method == 'POST':
        item = Item.objects.get(pk=request.POST['item_id'], shop=get_shop(request))
        values = dict(item.__dict__)
        for k in values.keys():
            if k.startswith('_') or k in ('id', 'baseitem_ptr_id'):
                values.pop(k)
        values['qty'] = 1
        values['bill'] = bill
        bitem = BillItem(**values)
        bitem.save()
        return view_bill(request, bill_id)
    items = Item.objects.filter(shop=get_shop(request))
    return render(request, "billing/add_item_to_bill.html", {'bill': bill, 'items': items})


def edit_item_in_bill(request, bill_id, item_id):
    bill = get_object_or_404(Bill, pk=bill_id, shop=get_shop(request))
    item = get_object_or_404(BillItem, pk=item_id, bill=bill, shop=get_shop(request))
    if not bill.can_be_modified():
        # The bill has been issued, and can't be modified
        raise Exception("The bill can't be modified")

    if request.method == 'POST':
        form = BillItemForm(request.POST, instance=item)
        if form.is_valid():
            form.save(commit=True)
            return view_bill(request, bill_id)
        else:
            print form.errors
    else:
        form = BillItemForm(instance=item)
    return render(request, "billing/edit_item_in_bill.html", {'form': form, 'bill_id': bill_id})

def delete_item_in_bill(request, bill_id, item_id):
    pass

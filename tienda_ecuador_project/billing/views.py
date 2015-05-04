from django.shortcuts import render, get_object_or_404
from models import Item, Bill, BillItem, ShopUser
from forms import ItemForm, BillForm
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


def index(request):
    items = Item.objects.all()
    bills = Bill.objects.all()
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
    new = Bill(shop=get_shop(request))
    new.save()
    return view_bill(new.fields.pk)


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
    pass

def edit_item_in_bill(request, bill_id, item_id):
    pass

def delete_item_in_bill(request, bill_id, item_id):
    pass

from django.shortcuts import render, get_object_or_404
from models import Item, Bill, BillItem, Shop, ShopUser
from forms import ItemForm

# Create your views here.
def get_current_shop(request):
    try:
        user = request.user
        shopuser = ShopUser.objects.get(user=user)
        return shopuser.shop
    except ShopUser.DoesNotExist:
        return None

def index(request):
    items = Item.objects.all()
    param_dict = {
        'items': items,
    }
    return render(request, "billing/index.html", param_dict)


def view_item(request, item_id):
    item_id = int(item_id)
    item = get_object_or_404(Item, pk=item_id)
    param_dict = {
        'item': item,
    }
    return render(request, "billing/view_item.html", param_dict)


def edit_item(request, item_id):
    item_id = int(item_id)
    item = get_object_or_404(Item, pk=item_id)
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


def view_bill(request, bill_id):
    bill_id = int(bill_id)
    bill = get_object_or_404(Bill, pk=bill_id)
    items = BillItem.objects.filter(bill=bill)
    param_dict = {
        'bill': bill,
        'items': items,
    }
    return render(request, "billing/view_bill.html", param_dict)

#Needs authentication
def new_bill(request):
    new = Bill(shop=get_current_shop(request))
    new.save()
    return view_bill(new.fields.pk)

def edit_bill(request, bill_id):
    bill_id = int(bill_id)
    bill = get_object_or_404(Bill, pk=bill_id)
    if bill.fields['number']:
        # The bill has been issued, and can't be modified
        return HttpResponse("The bill can't be modified")

    if request.method == 'POST':
        form = BillForm(request.POST, instance=bill)
        if form.is_valid():
            form.save(commit=True)
            return view_bill(request, bill_id)
        else:
            print form.errors
    else:
        form = BillForm(instance=item)
    return render(request, "billing/edit_bill.html", {'form': form, 'bill_id': bill_id})

    items = BillItem.objects.filter(bill=bill)
    param_dict = {
        'bill': bill,
        'items': items,
    }
    return render(request, "billing/view_bill.html", param_dict)

def delete_bill(request, bill_id):
    pass

def add_item_to_bill(request, bill_id):
    pass

def edit_item_in_bill(request, bill_id, item_id):
    pass

def delete_item_in_bill(request, bill_id, item_id):
    pass

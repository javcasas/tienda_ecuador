from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseForbidden, QueryDict
from models import Item, Bill, BillItem, CompanyUser, Company, Customer
from forms import ItemForm, BillForm, BillItemForm, CustomerForm
from django.contrib.auth.decorators import login_required
from functools import wraps
from django.views.generic import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse


@login_required
def index(request):
    """
    Shows an index for the current user,
    showing the companies he can administer
    If there is a single company,
    it redirects to the company automatically
    """
    c_user = CompanyUser.objects.filter(user=request.user)
    if len(c_user) == 1:
        return redirect("company_index", c_user[0].company.id)
    param_dict = {
        'companies': Company.objects.filter(id__in=[cu.id for cu in c_user]),
    }
    return render(request, "billing/index.html", param_dict)

def has_access_to_company(fn):
    """
    Decorator that checks the current user can use the company specified
    by company_id
    """
    @login_required
    @wraps(fn)
    def wrapper(request, **kwargs):
        company_id = kwargs.get('company_id')
        if company_id:
            get_object_or_404(
                CompanyUser, user=request.user, company_id=company_id
            )
        return fn(request, **kwargs)
    return wrapper

class BillingView(View):
    """
    Base class for views
    Checks:
        * That the user has access to the company
    """
    @classmethod
    def has_access_to_company(cls, fn):
        """
        Decorator that checks the current user can use the company specified
        by company_id
        """
        @login_required
        @wraps(fn)
        def wrapper(request, **kwargs):
            company_id = kwargs.get('company_id')
            if company_id:
                get_object_or_404(
                    CompanyUser, user=request.user, company_id=company_id
                )
            return fn(request, **kwargs)
        return wrapper

    def prepare_kwargs(self, request, kwargs):
        """
        Modifies kwargs to convert ids to instances or 404s
        Also generates a context dict ready to be used in render
        """
        company_id = kwargs.get('company_id')
        item_id = kwargs.get('item_id')
        customer_id = kwargs.get('customer_id')
        res = {}
        if company_id:
            get_object_or_404(  # Ensure has access to the company
                CompanyUser, user=request.user, company_id=company_id)
            res['company'] = get_object_or_404(Company, id=company_id)
            if item_id:
                res['item'] = get_object_or_404(Item, id=item_id, company_id=company_id)
            elif customer_id:
                res['customer'] = get_object_or_404(Customer, id=customer_id, company_id=company_id)
        return res

    def dispatch(self, request, *args, **kwargs):
        """
        Modified dispatch to apply:
            * prepare_kwargs
        """
        new_kwargs = self.prepare_kwargs(request, kwargs)
        return super(BillingView, self).dispatch(request, context=new_kwargs, **new_kwargs)

    @classmethod
    def as_view(cls, **initkwargs):
        """
        modified as_view to apply:
            * has_access_to_company
        """
        view = super(BillingView, cls).as_view(**initkwargs)
        view = has_access_to_company(view)
        return view


class CompanyIndex(BillingView):
    def get(self, request, context, company):
        """
        Shows an index for a company
        """
        context['items'] = Item.objects.filter(company=company)
        context['bills'] = Bill.objects.filter(company=company)
        context['customers'] = Customer.objects.filter(company=company)
        return render(request, "billing/company_index.html", context)


class ItemListView(ListView):
    model = Item
    context_object_name = "item_list"
    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(ItemListView, self).get_context_data(**kwargs)
        context['item_list'] = Item.objects.filter(company_id=self.kwargs['company_id'])
        context['company'] = self.company
        return context


class ItemDetailView(DetailView):
    model = Item
    context_object_name = 'item'
    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class ItemCreateView(CreateView):
    model = Item
    fields = ['sku', 'name', 'description']
    context_object_name = 'item'
    template_name_suffix = '_create_form'
    form = ItemForm

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def form_valid(self, form):
        form.instance.company = self.company
        return super(ItemCreateView, self).form_valid(form)


class ItemUpdateView(UpdateView):
    model = Item
    fields = ['sku', 'name', 'description']
    context_object_name = 'item'
    form = ItemForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context
    

class ItemDeleteView(DeleteView):
    model = Item
    context_object_name = 'item'

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    @property
    def success_url(self):
        return reverse("item_index", args=(self.company.id, ))
            
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context


class CustomerListView(ListView):
    model = Customer
    context_object_name = "customer_list"

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['customer_list'] = self.model.objects.filter(company_id=self.kwargs['company_id'])
        context['company'] = self.company
        return context


class CustomerDetailView(DetailView):
    model = Customer
    context_object_name = 'customer'

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context


class CustomerCreateView(CreateView):
    model = Customer
    fields = ['name', ]
    context_object_name = 'customer'
    template_name_suffix = '_create_form'
    form = CustomerForm

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = self.company
        return context

    def form_valid(self, form):
        form.instance.company = self.company
        return super(self.__class__, self).form_valid(form)


class CustomerUpdateView(UpdateView):
    model = Customer
    fields = ['name',]
    context_object_name = 'customer'
    form = CustomerForm

    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context
    

class CustomerDeleteView(DeleteView):
    model = Customer
    context_object_name = 'customer'

    @property
    def company(self):
        return get_object_or_404(Company, id=self.kwargs['company_id'])

    @property
    def success_url(self):
        view_name = "{}_index".format(self.context_object_name)
        return reverse(view_name, args=(self.company.id, ))
            
    def get_context_data(self, **kwargs):
        context = super(self.__class__, self).get_context_data(**kwargs)
        context['company'] = get_object_or_404(Company, id=self.kwargs['company_id'])
        return context


















class CustomerView(BillingView):
    entity = 'customer'
    form = CustomerForm
    entity_path = ['company']  # The expected parameters

    @classmethod
    def as_view(cls, **initkwargs):
        """
        Used as creator, like __init__
        """
        cls.index_template = 'billing/{}_view.html'.format(cls.entity)
        cls.view_template = 'billing/{}_view.html'.format(cls.entity)
        cls.edit_template = 'billing/{}_edit.html'.format(cls.entity)
        cls.view_name = '{}_view'.format(cls.entity)
        cls.index_name = '{}_index'.format(cls.entity)
        return super(CustomerView, cls).as_view(**initkwargs)

    def sanitise_parameters(self, request, kwargs):
        """
        @param:
            kwargs: dict
        Returns a tuple (main param, sanitised kwargs)
        """
        method = request.method.lower()
        # Make query dict
        if method == 'get':
            query = request.GET.copy()
        elif method == 'post':
            query = request.POST.copy()
        elif method in ['put', 'delete']:
            query = QueryDict(request.body).copy()
        else:
            raise ValueError("Unknown request method: ", method)
        # Make a new context
        newcontext = {}
        # Check if the optional entity exists
        ob = kwargs.pop(self.entity, None)
        query[self.entity] = ob
        # Copy the old context to the new
        try:
            for item in self.entity_path:
                newcontext[item] = kwargs.pop(item)
                query[item] = newcontext[item]
        except KeyError:
            raise TypeError("Missing parameter in {}(): {} ".format(method, item))
        # Ensure no stuff is left from the old context
        if kwargs:
            raise TypeError("{}() got an unexpected keyword argument: ".format(method, kwargs.keys()[0]))
        # Add the entry to the new context
        newcontext[self.entity] = ob
        return ob, newcontext, query

    def get(self, request, context, **kwargs):
        """
        Generic get
        """
        ob, context, data = self.sanitise_parameters(request, kwargs)
        # Select the template
        template = self.view_template if ob else self.index_template
        # Render
        return render(request, template, context)

    def post(self, request, context, **kwargs):
        """
        Generic post
        """
        ob, context, query = self.sanitise_parameters(request, kwargs)
        company = context['company']
        query['company'] = company.id
        if ob:
            query[self.entity] = context[self.entity].id
        form = self.form(query, instance=ob)
        if form.is_valid():
            new = form.save()
            return redirect(self.view_name, company.id, new.id)
        else:
            context['form'] = form
            return render(request, self.edit_template, context)

    def put(self, request, context, **kwargs):
        """
        update an inventory item
        """
        ob, context, query = self.sanitise_parameters(request, kwargs)
        company = context['company']
        query['company'] = company.id
        query[self.entity] = context[self.entity].id
        form = self.form(query, instance=ob)
        if form.is_valid():
            form.save()
            return redirect(self.view_name, company.id, ob.id)
        else:
            context['form'] = form
            return render(request, self.edit_template, context)

    def delete(self, request, context, company, customer):
        """
        delete an inventory item
        """
        customer.delete()
        return redirect('customer_index', company.id)

# class EditItem(ItemSelectedMixin):
    # template = "billing/edit_item.html"
    # form_class = ItemForm
# 
    # @ItemSelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id, item_id):
        # """
        # Edit an inventory item
        # """
        # param_dict = self.base_param_dict
        # param_dict['form'] = self.form_class(instance=param_dict['item'])
        # return render(request, self.template, param_dict)
# 
    # @ItemSelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id, item_id):
        # """
        # Edit and submit an inventory item
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['item'])
        # if form.is_valid():
            # form.save(commit=True)
            # return redirect("view_item", company_id, item_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class ViewBill(BillSelectedMixin):
    # @BillSelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id, bill_id):
        # """
        # View a bill
        # """
        # return render(request, "billing/view_bill.html", self.base_param_dict)
# 
# 
# class NewBill(CompanySelectedMixin):
    # @CompanySelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id):
        # """
        # Create a new bill
        # """
        # customer, created = Customer.objects.get_or_create(
            # name='Consumidor Final',
            # company=self.base_param_dict['company'],
        # )
        # new = Bill(company_id=company_id, customer_name=customer.name)
        # new.save()
        # return redirect("view_bill", company_id, new.id)
# 
# 
# class EditBill(BillSelectedMixin):
    # template = "billing/edit_bill.html"
    # form_class = BillForm
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id):
        # """
        # Edit a bill
        # """
        # param_dict = self.base_param_dict
        # param_dict['form'] = self.form_class(instance=param_dict['bill'])
        # return render(request, self.template, param_dict)
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Edit and submit a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['bill'])
        # if form.is_valid():
            # form.save(commit=True)
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class DeleteBill(BillSelectedMixin):
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Delete a bill
        # """
        # bill = self.base_param_dict['bill']
        # for item in bill.items:
            # item.delete()
        # bill.delete()
        # return redirect("company_index", company_id)
# 
# 
# class AddItemToBill(BillSelectedMixin):
    # form_class = BillItemForm
    # template = "billing/add_item_to_bill.html"
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id):
        # """
        # Add an item to a bill
        # """
        # param_dict = self.base_param_dict
        # data = {
            # 'bill': bill_id,
            # 'company': company_id,
        # }
        # param_dict['form'] = self.form_class(data)
        # return render(request, self.template, param_dict)
# 
    # @BillSelectedMixin.prepare_base_param_dict
    # @BillSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id):
        # """
        # Add an item and submit to a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST)
        # if form.is_valid():
            # form.save()
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class EditItemInBill(BillItemSelectedMixin):
    # form_class = BillItemForm
    # template = "billing/edit_item_in_bill.html"
# 
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def get(self, request, company_id, bill_id, item_id):
        # """
        # Edit an item in a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(instance=param_dict['item'])
        # param_dict['form'] = form
        # return render(request, self.template, param_dict)
# 
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id, item_id):
        # """
        # Edit an item and submit in a bill
        # """
        # param_dict = self.base_param_dict
        # form = self.form_class(request.POST, instance=param_dict['item'])
        # if form.is_valid():
            # form.save()
            # return redirect("view_bill", company_id, bill_id)
        # else:
            # param_dict['form'] = form
            # return render(request, self.template, param_dict)
# 
# 
# class DeleteItemFromBill(BillItemSelectedMixin):
    # @BillItemSelectedMixin.prepare_base_param_dict
    # @BillItemSelectedMixin.check_bill_can_be_modified
    # def post(self, request, company_id, bill_id, item_id):
        # """
        # Delete an item from a bill
        # """
        # param_dict = self.base_param_dict
        # param_dict['item'].delete()
        # return redirect("view_bill", company_id, bill_id)
# 
# 
# class NewCustomer(CompanySelectedMixin):
    # form_class = CustomerForm
# 
    # @CompanySelectedMixin.prepare_base_param_dict
    # def get(self, request, company_id):
        # """
        # Shows a form to create new customers
        # """
        # param_dict = self.base_param_dict
        # param_dict['new'] = True
        # data = {
            # 'company': company_id,
        # }
        # param_dict['form'] = self.form_class(data)
        # return render(request, "billing/edit_customer.html", param_dict)
# 
    # @CompanySelectedMixin.prepare_base_param_dict
    # def post(self, request, company_id):
        # """
        # Accepts submit
        # """
        # form = self.form_class(request.POST)
        # if form.is_valid():
            # form.save()
            # return redirect("company_index", company_id)
        # else:
            # param_dict = self.base_param_dict
            # param_dict['form'] = form
            # return render(request, "billing/edit_customer.html", param_dict)

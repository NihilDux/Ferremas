from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto, Categoria, CustomUser, CarritoItem
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import IntegrityError
from django.db.models import Q
from .forms import ProductoForm
import locale
from datetime import datetime
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError
from src.services.localApi import get_users, get_money, get_products, get_categories, get_product_by_id
import json

from django.http import HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseServerError
from transbank.webpay.webpay_plus.transaction import Transaction, TransbankError
from transbank.common.integration_commerce_codes import IntegrationCommerceCodes
from transbank.common.integration_type import IntegrationType
from transbank.common.integration_api_keys import IntegrationApiKeys
from transbank.common.options import WebpayOptions

import requests
from django.http import JsonResponse

def home(request): #Solo inicio de la página
    productos = Producto.objects.filter(aprobado=True, relevante=True).order_by('-aprobado')
    categorias = Categoria.objects.all()
    usuarios = get_users()
    moneda = get_money()
    
    if request.user.is_authenticated:
        user = request.user
        productos_by_user = productos.filter(user=user)
        num_productos = productos_by_user.count()
        
        context = {
            'productos': productos,
            'num_productos': num_productos,
            'categorias': categorias,
            #'usuarios': usuarios
        }
        return render(request, 'home.html', context)
    else:
        context = {
            'productos': productos,
            'categorias': categorias,
            'usuarios': usuarios,
        }
        return render(request, 'home.html', context)
    
def productos(request):

    productos2 = get_products()
    print(f'Productos: {productos2}')
    categorias2 = get_categories()
    dolar = get_money()
    #print(f'El Dolar es :{dolar}')
    
    only_dolar = dolar['Dolares'][0]['Valor']
    only_date = dolar['Dolares'][0]['Fecha']

    for producto2 in productos2:
        dolarito = dolar['Dolares'][0]['Valor']
        dolarito = dolarito.replace(',', '.')
        producto2['precio_dolar'] = round(int(producto2['precio']) / float(dolarito), 2)

    context = {
        'productos2': productos2,
        'categorias2': categorias2,
        'dolar': only_dolar,
        'fecha': only_date
    }
    return render(request, 'productos.html', context)
    
    
#@login_required   #Desactivado para pruebas    
def registrar(request):
    if request.method == 'GET':
        return render(request, 'registrar.html',{
            'form': UserCreationForm
        })
    else:
        if request.POST['password1'] == request.POST['password2']:
            try:
                user = CustomUser.objects.create_user(username=request.POST['username'], email=request.POST['email'], password=request.POST['password1'])
                user.save()
                login(request, user)
                return redirect('home')
            except IntegrityError:
                return render(request, 'registrar.html',{
                    'form': UserCreationForm,
                    "error": 'Usuario ya existe'
                })
        return render(request, 'registrar.html',{
                    'form': UserCreationForm,
                    "error": 'Contraseñas no coinciden.'
                })  
   

#VISA TEST 4051 8856 0044 6623
def checkout(request):
    if request.method == 'POST':
        print("Creando compra...")
        order = "ordenCompra123456"
        session = "sesion1234557545"
        amount = request.POST.get('total_carrito')
        return_url = "http://127.0.0.1:8000/checkout"

        tx = Transaction(WebpayOptions(api_key=IntegrationApiKeys.WEBPAY, commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS, integration_type=IntegrationType.TEST))
        
        try:
            response = tx.create(buy_order=order, session_id=session, amount=amount, return_url=return_url)
            #print(response)
            return redirect(response['url'] + '?token_ws=' + response['token'])
        
        except TransbankError as e:
            print(f"Error al crear transacción: {e.message}, código: {e.code}")
            return HttpResponseServerError("Error al procesar la transacción")

    elif request.method == 'GET':
        tx = Transaction(WebpayOptions(api_key=IntegrationApiKeys.WEBPAY, commerce_code=IntegrationCommerceCodes.WEBPAY_PLUS, integration_type=IntegrationType.TEST))
        token = request.GET.get('token_ws')

        if not token:
            print("No se ha recibido el token_ws")
            return HttpResponseBadRequest("Token_ws no recibido")

        try:
            resp = tx.commit(token)
            print(resp)

            if resp['status'] == "AUTHORIZED":
                print("Autorizado")
                
                carrito = request.session.get('carrito', {})
                productos_para_api = [{'producto_id': producto_id, 'cantidad': detalle_producto['cantidad']} for producto_id, detalle_producto in carrito.items()]
                
                api_url = "http://127.0.0.1:5000/post/productos/subtract_stock"
                response = requests.post(api_url, json={'productos': productos_para_api})

                if response.status_code != 200:
                    print("Error al actualizar el stock en la API")
                    return HttpResponseServerError("Error al actualizar el stock en la API")
            elif resp['status'] == "FAILED":
                print("Fallido")
            else:
                print("Estado desconocido")

            return render(request, 'checkout.html', {'resp': resp})

        except TransbankError as e:
            print(f"Error al confirmar transacción: {e.message}, código: {e.code}")
            return HttpResponseServerError("Error al procesar la transacción")

    else:
        return HttpResponseNotAllowed(['POST', 'GET'])

# def carrito(request):
#     # Obtener el carrito del request
#     carrito = request.session.get('carrito', {})
#     items = []
#     total_carrito = 0
    
#     # Recorrer los elementos del carrito y calcular el total
#     for item_id, quantity in carrito.items():
#         product = get_object_or_404(Producto, pk=item_id)
#         subtotal = product.precio * quantity
#         items.append({'id':item_id,'product': product, 'quantity': quantity,
#                       'precio': product.precio,'imagen':product.imagen, 'subtotal': subtotal})
#         total_carrito += subtotal
#     return render(request, 'carrito.html', {'items': items, 'total_carrito': total_carrito})

def carrito(request):
    carrito = request.session.get('carrito', {})
    productos_en_carrito = []

    total_carrito = 0
    for producto_id, detalle_producto in carrito.items():
        subtotal = detalle_producto['precio_unitario'] * detalle_producto['cantidad']
        total_carrito += subtotal

        productos_en_carrito.append({
            'producto_id': producto_id,
            'nombre': detalle_producto['nombre'],
            'imagen': detalle_producto['imagen'],
            'precio_unitario': detalle_producto['precio_unitario'],
            'cantidad': detalle_producto['cantidad'],
            'subtotal': subtotal
        })
        print(productos_en_carrito)

    return render(request, 'carrito.html', {
        'productos_en_carrito': productos_en_carrito,
        'total_carrito': total_carrito
    })

def agregar_al_carrito(request, producto_id):
    # Lógica para agregar productos al carrito utilizando cookies
    producto = get_product_by_id(producto_id)
    
    print(producto)
    print('------------------------------------')
    if producto:
        carrito = request.session.get('carrito', {})
        
        if producto_id in carrito:
            carrito[producto_id]['cantidad'] += 1
        else:
            carrito[producto_id] = {
                'nombre': producto['nombre'],
                'imagen': producto['imagen'],
                'precio_unitario': producto['precio'],
                'cantidad': 1
            }
        
        request.session['carrito'] = carrito
    
    return redirect('carrito')

def vaciar_carrito(request):
    if 'carrito' in request.session:
        del request.session['carrito']
    return redirect('carrito')

def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)  # Aseguramos que producto_id es una cadena
    
    if producto_id_str in carrito:
        del carrito[producto_id_str]
        request.session['carrito'] = carrito
    
    return redirect('carrito')

def aumentar_cantidad(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)
    
    if producto_id_str in carrito:
        carrito[producto_id_str]['cantidad'] += 1
    
    request.session['carrito'] = carrito
    return redirect('carrito')

def disminuir_cantidad(request, producto_id):
    carrito = request.session.get('carrito', {})
    producto_id_str = str(producto_id)
    
    if producto_id_str in carrito:
        if carrito[producto_id_str]['cantidad'] > 1:
            carrito[producto_id_str]['cantidad'] -= 1
        else:
            del carrito[producto_id_str]  # Opción para eliminar si la cantidad es 0 o menos
    
    request.session['carrito'] = carrito
    return redirect('carrito')

#Algo pasa acá >:)
urlapi = 'https://api-ferramas.onrender.com/api'


def ingreso(request):
    global urlapi
    
    if request.method == 'GET':
        return render(request, 'ingreso.html',{
            'form': AuthenticationForm
         })
    else:
        mail=request.POST['username']

        password=request.POST['password']
        
        
        data = {
            "mail": mail,
            "password": password
        }
        
        response = requests.post(f'{urlapi}/auth', json=data)

        print(response.text)
        return redirect('home')  
   
   
def cerrar(request):
    logout(request)
    CarritoItem.objects.all().delete()
    return redirect('home')  
   
#@login_required 
def crear(request):
    if request.method == 'POST':
        try:
            form = ProductoForm(request.POST, request.FILES)
            rol = request.user.rol
            if form.is_valid():
                if user_passes_test(rol == 'admin' or rol == 'bodeguero' or rol == 'vendedor'): # Revisar condiciones
                    new_product = form.save(commit=False)
                    new_product.user = request.user
                    new_product.save()
                    print(request.POST, request.FILES)
                    return redirect('home')
        except ValueError:
            print(request.POST)
            return render(request, 'crear.html', {
                'form': ProductoForm(),
                'error': 'Por favor, valide los datos'
            })
    else:
        return render(request, 'crear.html', {
            'form': ProductoForm(),
        })
        
def detalle(request, product_id):
        product = get_object_or_404(Producto, pk=product_id)
        form = ProductoForm(instance=product)
        return render(request, 'detalle.html',{
            'product':product,
            'form': form
            }) 
        
        
def actualizar(request, product_id):
    if request.method == 'GET':
        product = get_object_or_404(Producto, pk=product_id)
        form = ProductoForm(instance=product)
        return render(request, 'detalle_producto.html',{
            'product':product,
            'form': form
            })
    else:
        try:
            product = get_object_or_404(Producto, pk=product_id)
            form = ProductoForm(request.POST, instance=product)
            form.save()
            return redirect('products')
        except ValueError:
                return render(request, 'detalle_producto.html',{
                'product':product,
                'form': form,
                'error': 'Error al Actualizar'
                }) 
   
def productos_por_categoria(request, categoria_id):
    categoria = get_object_or_404(Categoria, id_categoria=categoria_id)
    productos_categoria = Producto.objects.filter(id_categoria=categoria)
    for producto in productos_categoria:
        producto.precio_formateado = locale.format_string("%d", producto.precio, grouping=True)

    context = {
        'categorias': categoria,
        'productos': productos_categoria
    }
    return render(request, 'productos_por.html', context)   
   
def contacto(request):
    return render(request, 'contacto.html', { 
    })
    # if request.method == 'POST':

    #     return render(request, 'contacto.html', {
            
    #         'mensaje': 'Enviado Correctamente',
    #         'script' : 'window.onload = function() {formu()};'      
    #     }, print(request.POST))
    # else:
    #     return render(request, 'contacto.html', { 
    #     })  
  
      


  
def buscar(request):
    if request.method == 'GET':
        query = request.GET.get("q")
        if not query:
            context = {'query': query}
            return render(request, 'resultado_busqueda.html', context)

        resultados = Producto.objects.filter(
            Q(user__username__icontains=query) |  # Buscar por nombre de usuario del artista
            Q(titulo__icontains=query) |  # Buscar por título
            Q(id_categoria__categoria__icontains=query)  # Buscar por categoría
        )

        context = {'resultados': resultados, 'query': query}
        return render(request, 'resultado_busqueda.html', context)
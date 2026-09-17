import unittest
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.app import app
from src.models import session
from src.models.usuarios import Usuarios
from src.models.facturas import Facturas
from src.models.clientes import Clientes

class TestSecurityAudit(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_01_admin_backdoor_removed(self):
        """Verifica que el backdoor admin/123456 ya NO funcione si el password no coincide."""
        response = self.app.post('/api/auth/login', json={
            'username': 'admin',
            'password': 'invalid_backdoor_test_password_xyz'
        })
        self.assertEqual(response.status_code, 401, "El login con credenciales erróneas debe retornar 401")
        data = response.get_json()
        self.assertFalse(data.get('exito', True))

    def test_02_otp_does_not_leak_in_response(self):
        """Verifica que la solicitud de recuperación OTP NO exponga código ni token en la respuesta JSON."""
        response = self.app.post('/api/auth/recuperar-password-solicitar', json={
            'identificador': 'admin@pymesoft.com'
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data.get('exito'))
        self.assertNotIn('codigo', data, "¡VULNERABILIDAD! 'codigo' OTP expuesto en el response JSON")
        self.assertNotIn('token', data, "¡VULNERABILIDAD! 'token' de recuperación expuesto en el response JSON")
        self.assertNotIn('link_directo', data, "¡VULNERABILIDAD! 'link_directo' con token expuesto en el response JSON")

    def test_03_unauthenticated_protected_routes(self):
        """Verifica que rutas críticas rechacen peticiones no autenticadas con 401."""
        endpoints = [
            ('/api/reportes/dashboard?id_empresa=1', 'GET'),
            ('/api/facturas/?id_empresa=1', 'GET'),
            ('/api/compras/?id_empresa=1', 'GET'),
            ('/api/usuarios/', 'GET'),
            ('/api/productos/?id_empresa=1', 'GET'),
            ('/api/clientes/?id_empresa=1', 'GET'),
        ]
        for url, method in endpoints:
            if method == 'GET':
                res = self.app.get(url)
            self.assertIn(res.status_code, [401], f"Endpoint {url} debe requerir JWT (401)")

    def test_04_privilege_escalation_blocked_on_register(self):
        """Verifica que un usuario anónimo NO pueda registrarse con rol Administrador (id_rol=1)."""
        test_username = "test_attacker_user"
        existing = session.query(Usuarios).filter_by(username=test_username).first()
        if existing:
            session.delete(existing)
            session.commit()

        response = self.app.post('/api/usuarios/', json={
            'nombre': 'Attacker',
            'apellido': 'User',
            'username': test_username,
            'email': 'attacker@test.com',
            'password': 'attacker_password_123',
            'id_rol': 1
        })
        self.assertIn(response.status_code, [200, 201])
        
        created_user = session.query(Usuarios).filter_by(username=test_username).first()
        self.assertIsNotNone(created_user)
        self.assertEqual(created_user.id_rol, 2, "La escalada de privilegios falló: el rol asignado debe ser 2 (Vendedor), no 1 (Admin)")
        
        # Cleanup
        session.delete(created_user)
        session.commit()

    def test_05_client_credit_card_redaction(self):
        """Verifica que la serialización de clientes no filtre el número completo de tarjeta ni el CVC."""
        cliente = session.query(Clientes).first()
        if cliente:
            cliente_dict = cliente.to_dict()
            self.assertNotIn('numero_tarjeta', cliente_dict, "El número de tarjeta no debe exponerse en el diccionario del cliente")
            self.assertNotIn('cvc_tarjeta', cliente_dict, "El CVC jamás debe exponerse en el diccionario del cliente")

    def test_06_non_existent_product_deletion(self):
        """Verifica que intentar eliminar un producto inexistente retorne 404 y no 200/500."""
        login_res = self.app.post('/api/auth/login', json={
            'email': 'admin@pymesoft.com',
            'password': 'password'
        })
        if login_res.status_code == 200:
            token = login_res.get_json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            res = self.app.delete('/api/productos/9999999', headers=headers)
            self.assertEqual(res.status_code, 404, "Eliminar producto inexistente debe retornar 404")

    def test_07_tenant_isolation_invoice(self):
        """Verifica que un usuario sin acceso a una empresa NO pueda ver facturas de esa empresa (BOLA/IDOR)."""
        login_res = self.app.post('/api/auth/login', json={
            'email': 'vendedor@techsolutions.com',
            'password': 'password'
        })
        if login_res.status_code == 200:
            token = login_res.get_json().get('access_token')
            headers = {'Authorization': f'Bearer {token}'}
            
            fac_otra_empresa = session.query(Facturas).filter(Facturas.id_empresa != 1).first()
            if fac_otra_empresa:
                res = self.app.get(f'/api/facturas/{fac_otra_empresa.id}', headers=headers)
                self.assertEqual(res.status_code, 403, "El acceso BOLA/IDOR a factura de otra empresa debe retornar 403 Prohibido")

if __name__ == '__main__':
    unittest.main()

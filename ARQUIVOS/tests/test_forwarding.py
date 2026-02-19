from django.test import TestCase
from ARQUIVOS.models import Administracao, Departamento, CustomUser, Documento, TipoDocumento
from ARQUIVOS.hierarchy_manager import HierarchyManager

class ForwardingLogicTest(TestCase):
    def setUp(self):
        # 1. Criar Administrações
        self.mat = Administracao.objects.create(
            nome="Ministério da Administração do Território",
            tipo_municipio='M',
            provincia='Luanda'
        )
        self.gov_uige = Administracao.objects.create(
            nome="Governo Provincial do Uíge",
            tipo_municipio='G',
            provincia='Uíge'
        )
        self.mun_uige = Administracao.objects.create(
            nome="Administração Municipal do Uíge",
            tipo_municipio='A',
            provincia='Uíge'
        )

        # 2. Criar Secretarias Gerais (necessárias para encaminhamento hierárquico)
        self.dept_sg_mat = Departamento.objects.create(
            nome="Secretaria Geral",
            administracao=self.mat,
            tipo_municipio='M'
        )
        self.dept_sg_gov = Departamento.objects.create(
            nome="Secretaria Geral",
            administracao=self.gov_uige,
            tipo_municipio='G'
        )

        # 3. Criar usuários
        # Case 1: Um administrador do Governo que NÃO está na Secretaria Geral
        self.dept_outro_gov = Departamento.objects.create(
            nome="Direcção de Recursos Humanos",
            administracao=self.gov_uige,
            tipo_municipio='G'
        )
        self.user_admin_gov = CustomUser.objects.create_user(
            username="admin_gov",
            password="password123",
            administracao=self.gov_uige,
            departamento=self.dept_outro_gov,
            nivel_acesso='admin_municipal'
        )

        # Case 2: Um utilizador comum do Governo (para contraste)
        self.user_comum_gov = CustomUser.objects.create_user(
            username="comum_gov",
            password="password123",
            administracao=self.gov_uige,
            departamento=self.dept_outro_gov,
            nivel_acesso='tecnico'
        )

    def test_admin_can_see_hierarchical_destinations(self):
        """Verifica se um administrador (não SG) pode ver destinos externos."""
        manager = HierarchyManager(self.user_admin_gov)
        
        # O administrador deve poder encaminhar externo
        self.assertTrue(manager.usuario_pode_encaminhar_externo(), 
                        "Administradores devem poder encaminhar externamente.")
        
        destinos = manager.obter_destinos_hierarquicos()
        # Governo do Uíge deve ver o MAT (M) e Municípios da mesma província
        self.assertIn(self.mat, destinos, "Governo deve ver o MAT como destino.")
        self.assertIn(self.mun_uige, destinos, "Governo deve ver Município da mesma província.")

    def test_common_user_cannot_see_hierarchical_destinations(self):
        """Verifica se um utilizador comum (não SG e não admin) NÃO vê destinos externos."""
        manager = HierarchyManager(self.user_comum_gov)
        
        self.assertFalse(manager.usuario_pode_encaminhar_externo(), 
                         "Utilizadores comuns não devem poder encaminhar externamente.")
        
        destinos = manager.obter_destinos_hierarquicos()
        self.assertEqual(destinos.count(), 0, "Utilizadores comuns não devem ter destinos hierárquicos.")

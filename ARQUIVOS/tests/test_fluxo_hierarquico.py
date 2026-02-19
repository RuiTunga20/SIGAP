from django.test import TestCase
from ARQUIVOS.models import CustomUser, Departamento, Seccoes, Documento, MovimentacaoDocumento, StatusDocumento, TipoDocumento, Administracao
from django.utils import timezone
from ARQUIVOS.formularios import EncaminharDocumentoForm, DistribuirDocumentoForm

class FluxoHierarquicoTests(TestCase):
    def setUp(self):
        # 1. Criar Administração
        self.admin = Administracao.objects.create(nome="Admin Teste", tipo_municipio="A", provincia="Luanda")
        
        # 2. Criar Estrutura Hierárquica
        self.dept = Departamento.objects.create(nome="Dept TI", administracao=self.admin)
        self.seccao = Seccoes.objects.create(nome="Secção Dev", departamento=self.dept)
        
        # 3. Criar TIPO DE DOCUMENTO
        self.tipo_doc = TipoDocumento.objects.create(nome="Ofício")

        # 4. Criar Usuários
        # TÉCNICO (Nível 0, Nível Sigilo 0)
        self.tecnico = CustomUser.objects.create_user(
            username='tecnico', password='123', 
            nivel_acesso='tecnico', nivel_sigilo=0,
            administracao=self.admin, departamento=self.dept, seccao=self.seccao
        )
        
        # CHEFE DA SECÇÃO (Nível 1, Chefia)
        self.chefe = CustomUser.objects.create_user(
            username='chefe', password='123',
            nivel_acesso='chefe_seccao', nivel_sigilo=1,
            administracao=self.admin, departamento=self.dept, seccao=self.seccao
        )
        
        # DIRETOR (Nível 2, Direção - Dept inteiro)
        self.diretor = CustomUser.objects.create_user(
            username='diretor', password='123',
            nivel_acesso='diretor_municipal', nivel_sigilo=2,
            administracao=self.admin, departamento=self.dept
        )

    def test_visibilidade_tecnico_restrita(self):
        """Teste se técnico vê apenas documentos atribuídos/próprios."""
        
        # Doc criado pelo Chefe
        doc_chefe = Documento.objects.create(
            titulo="Doc Chefe", tipo_documento=self.tipo_doc,
            criado_por=self.chefe, departamento_origem=self.dept,
            departamento_atual=self.dept, seccao_atual=self.seccao,
            administracao=self.admin
        )
        
        # Doc criado pelo Técnico
        doc_tecnico = Documento.objects.create(
            titulo="Doc Tecnico", tipo_documento=self.tipo_doc,
            criado_por=self.tecnico, departamento_origem=self.dept,
            departamento_atual=self.dept, seccao_atual=self.seccao,
            administracao=self.admin
        )

        # Verificar Visibilidade do TÉCNICO
        qs_tecnico = Documento.objects.para_usuario(self.tecnico)
        self.assertIn(doc_tecnico, qs_tecnico, "Técnico deve ver seu próprio documento")
        self.assertNotIn(doc_chefe, qs_tecnico, "Técnico NÃO deve ver documento do chefe não atribuído")
        
        # Verificar Visibilidade do CHEFE
        qs_chefe = Documento.objects.para_usuario(self.chefe)
        self.assertIn(doc_tecnico, qs_chefe, "Chefe deve ver documento do técnico (mesmo setor)")
        self.assertIn(doc_chefe, qs_chefe, "Chefe deve ver seu próprio documento")

    def test_distribuicao_documento(self):
        """Teste se distribuição (atribuição) torna documento visível ao técnico."""
        
        # Doc na secção, mas não do técnico
        doc = Documento.objects.create(
            titulo="Doc Para Distribuir", tipo_documento=self.tipo_doc,
            criado_por=self.chefe, departamento_origem=self.dept,
            departamento_atual=self.dept, seccao_atual=self.seccao,
            administracao=self.admin
        )
        
        # Técnico não vê inicialmente
        self.assertFalse(Documento.objects.para_usuario(self.tecnico).filter(id=doc.id).exists())
        
        # CHEFE Distribui (Simulação via Form/View logic)
        form_data = {'tecnico': self.tecnico.id, 'observacoes': 'Tratar urgente'}
        form = DistribuirDocumentoForm(data=form_data, user=self.chefe)
        self.assertTrue(form.is_valid(), f"Form inválido: {form.errors}")
        
        # Aplicar Atribuição
        doc.responsavel_atual = form.cleaned_data['tecnico']
        doc.save()
        
        # Técnico AGORA deve ver
        self.assertTrue(Documento.objects.para_usuario(self.tecnico).filter(id=doc.id).exists(), "Técnico deve ver documento após distribuição")

    def test_restricao_destinos_tecnico(self):
        """Teste se ao encaminhar, técnico tem opções restritas."""
        
        # Form para Técnico
        form = EncaminharDocumentoForm(user=self.tecnico, documento=None)
        
        # Verificar Queryset de Departamento e Secção
        # Técnico só pode enviar para o PRÓPRIO contexto (subir hierarquia)
        
        # Campos
        dept_field = form.fields['departamento_destino']
        seccao_field = form.fields['seccao_destino']
        
        # Como o técnico está numa SECÇÃO, ele DEVE ver apenas sua própria SECÇÃO na lista (para devolver à chefia)
        # OU ver NADA se a lógica for "apenas sobe".
        # Vamos verificar a lógica atual no Form/Manager.
        
        # Na logica atual: se em secção, sobe para secção? Não faz sentido. 
        # Sobe para o Chefe da Seção. O chefe da seção VÊ tudo da seção.
        # Então encaminhar para a PRÓPRIA seção é o correto.
        
        self.assertIn(self.seccao, seccao_field.queryset, "Técnico deve poder selecionar sua própria secção")
        self.assertEqual(seccao_field.queryset.count(), 1, "Técnico deve ver APENAS sua própria secção")
        
        # E Departamentos?
        self.assertEqual(dept_field.queryset.count(), 0, "Técnico em secção não deve ver departamentos diretos")

    def test_permissoes_usuario(self):
        """Teste propriedades auxiliares como eh_tecnico e pode_distribuir."""
        self.assertTrue(self.tecnico.eh_tecnico)
        self.assertFalse(self.tecnico.pode_distribuir())
        
        self.assertFalse(self.chefe.eh_tecnico)
        self.assertTrue(self.chefe.pode_distribuir())
        
        self.assertFalse(self.diretor.eh_tecnico)
        self.assertTrue(self.diretor.pode_distribuir())

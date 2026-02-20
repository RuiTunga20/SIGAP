# forms_refactored.py
"""
Formulários refatorados usando HierarchyManager centralizado.

Substitui a lógica duplicada por chamadas ao HierarchyManager,
que funciona igualmente para encaminhamento, criação de usuário, etc.
"""

from django.contrib.auth.forms import UserCreationForm
from django.db.models import Q
from django import forms
from django.core.exceptions import ValidationError
from tinymce.widgets import TinyMCE

from .models import (
    Documento,
    CustomUser,
    Departamento,
    MovimentacaoDocumento,
    Seccoes,
    StatusDocumento,
    TipoDocumento,
    Anexo,
    ArmazenamentoDocumento,
    LocalArmazenamento,
    Administracao,
)

# Importar o gerenciador centralizado
from .hierarchy_manager import (
    HierarchyManager,
    validar_destino_encaminhamento,
    obter_label_dinamico,
    obter_secretaria_geral,
    _get_contexto_usuario,
)


# ===========================================================================
# DocumentoForm (sem mudanças significativas)
# ===========================================================================

class DocumentoForm(forms.ModelForm):
    """
    Formulário para criação e edição de documentos
    """

    class Meta:
        model = Documento
        fields = [
            'titulo', 'tipo_documento', 'prioridade',
            'arquivo', 'arquivo_digitalizado', 'tags',
            'utente', 'telefone', 'email', 'origem', 'niveis', 'referencia',
        ]
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite o título do documento',
                'maxlength': '200',
                'required': True,
            }),
            'utente': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite o Nome',
                'maxlength': '200',
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-input',
                'placeholder': 'Digite o Email',
                'maxlength': '200',
                'required': True,
            }),
            'tipo_documento': forms.Select(attrs={'class': 'form-select'}),
            'prioridade': forms.Select(attrs={
                'class': 'form-select',
            }),
            'arquivo': forms.FileInput(attrs={
                'class': 'file-input',
                'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png'
            }),
            'arquivo_digitalizado': forms.FileInput(attrs={
                'class': 'file-input',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'O numero do Armario pasta  Armario-1/doc-335',
                'maxlength': '500'
            }),
        }


# ===========================================================================
# EncaminharDocumentoForm (REFATORADO COM HierarchyManager)
# ===========================================================================

class EncaminharDocumentoForm(forms.ModelForm):
    """
    Formulário para encaminhar documentos.
    
    Usa HierarchyManager para calcular departamentos e secções permitidos,
    funcionando para TODOS os tipos de usuário (admin, dept, secção, superuser).
    """

    class Meta:
        model = MovimentacaoDocumento
        fields = [
            'tipo_movimentacao',
            'departamento_destino',
            'seccao_destino',
            'observacoes',
            'despacho',
        ]
        widgets = {
            'observacoes': TinyMCE(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Observações sobre o encaminhamento...',
            }),
            'despacho': TinyMCE(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': 'Despacho oficial...',
            }),
            'tipo_movimentacao': forms.Select(attrs={'class': 'form-control'}),
            'departamento_destino': forms.Select(attrs={
                'class': 'form-control',
                'data-exclusive': 'seccao_destino,destino_hierarquico,destino_municipal'
            }),
            'seccao_destino': forms.Select(attrs={
                'class': 'form-control',
                'data-exclusive': 'departamento_destino,destino_hierarquico,destino_municipal'
            }),
        }

    destino_hierarquico = forms.ModelChoiceField(
        queryset=Administracao.objects.none(),
        required=False,
        label='Governo / MAT',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-exclusive': 'departamento_destino,seccao_destino,destino_municipal'
        })
    )

    destino_municipal = forms.ModelChoiceField(
        queryset=Administracao.objects.none(),
        required=False,
        label='Administração Municipal',
        widget=forms.Select(attrs={
            'class': 'form-control',
            'data-exclusive': 'departamento_destino,seccao_destino,destino_hierarquico'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user      = kwargs.pop('user', None)
        self.documento = kwargs.pop('documento', None)
        super().__init__(*args, **kwargs)

        if self.documento:
            self.instance.documento = self.documento

        self.fields['tipo_movimentacao'].choices = [
            ('criacao',        'Criar'),
            ('encaminhamento', 'Encaminhar'),
        ]

        self.fields['departamento_destino'].required = False
        self.fields['seccao_destino'].required = False

        # Usar HierarchyManager para popular querysets
        if self.user:
            manager = HierarchyManager(self.user)
            
            # Obter destinos
            self.show_external = manager.usuario_pode_encaminhar_externo()
            # Filtro de Técnicos de Secção (Nível 0)
            # Regra: Técnico não encaminha para fora. Só DEVOLVE à chefia da sua secção.
            if getattr(self.user, 'eh_tecnico', False) and getattr(self.user, 'seccao', None):
                # Técnico de Secção: vê APENAS a própria secção (para devolver à chefia).
                # Não vê departamentos nem destinos externos.
                qs_hierarquico = Administracao.objects.none()
                qs_dept_permitidos = Departamento.objects.none()
                qs_sec = Seccoes.objects.filter(pk=self.user.seccao.pk)
                seccoes_fixas = True
            else:
                qs_hierarquico = manager.obter_destinos_hierarquicos()
                qs_dept_permitidos, qs_sec, seccoes_fixas = manager.obter_destinos_permitidos(incluir_self=False)
            
            # Filtrar departamentos para serem apenas INTERNOS (mesma administração)
            qs_dept_interno = qs_dept_permitidos.filter(administracao=self.user.administracao)
            
            # Verificar se é Secretaria Geral de um Governo
            # CORREÇÃO: Evitar erro "Cannot combine a unique query with a non-unique query"
            # O `qs_dept_permitidos` pode vir com distinct(), então o operador | falha.
            # Convertemos para lista de IDs para garantir segurança.
            ids_permitidos = list(qs_dept_interno.values_list('pk', flat=True))
            
            # CORREÇÃO PARA CHEFES DE SECÇÃO (Nível 1):
            if getattr(self.user, 'nivel_sigilo', 0) >= 1 and getattr(self.user, 'seccao', None):
                dept_pai = self.user.seccao.departamento
                if dept_pai and dept_pai.pk not in ids_permitidos:
                     ids_permitidos.append(dept_pai.pk)
            
            # Recriar queryset limpo
            qs_dept_interno = Departamento.objects.filter(pk__in=ids_permitidos)
            
            qs_dept_interno = qs_dept_interno.distinct().order_by('nome')
            
            # Verificar se é Secretaria Geral de um Governo
            from .hierarchy_manager import _is_secretaria_geral
            user_admin = self.user.administracao
            is_gov = user_admin and user_admin.tipo_municipio == 'G'
            is_sec_geral = _is_secretaria_geral(getattr(self.user, 'departamento_efetivo', None))
            self.is_governo_secretaria = is_gov and is_sec_geral and self.show_external
            
            if self.is_governo_secretaria:
                # Separar destinos: Governos/MAT vs Administrações Municipais
                self.fields['destino_hierarquico'].queryset = qs_hierarquico.filter(
                    tipo_municipio__in=['G', 'M']
                )
                self.fields['destino_municipal'].queryset = qs_hierarquico.exclude(
                    tipo_municipio__in=['G', 'M']
                )
            else:
                self.fields['destino_hierarquico'].queryset = qs_hierarquico
                self.fields['destino_municipal'].queryset = Administracao.objects.none()
            
            self.fields['departamento_destino'].queryset = qs_dept_interno
            self.fields['seccao_destino'].queryset = qs_sec
            
            # Customizar labels para omitir administração se for a do usuário (limpeza visual)
            user_admin = self.user.administracao
            
            def dept_label(obj):
                if user_admin and obj.administracao == user_admin:
                    return obj.nome
                return f"{obj.nome} ({obj.administracao.nome if obj.administracao else '?'})"
                
            def sec_label(obj):
                if user_admin and obj.administracao == user_admin:
                    return obj.nome
                return f"{obj.nome} [{obj.administracao.nome if obj.administracao else '?'}]"

            self.fields['departamento_destino'].label_from_instance = dept_label
            self.fields['seccao_destino'].label_from_instance = sec_label
            
            # Armazenar para uso no template
            self.seccoes_fixas = seccoes_fixas
            
            # Preparar dados JSON para JavaScript
            if not seccoes_fixas:
                self.seccoes_data = {}
                if qs_dept_interno.exists():
                    for d in qs_dept_interno:
                        self.seccoes_data[d.pk] = list(
                            Seccoes.objects.filter(departamento=d).values('id', 'nome')
                        )
            else:
                self.seccoes_data = None

            # Labels dinâmicos
            labels = obter_label_dinamico(self.user, contexto='encaminhamento')
            self.fields['destino_hierarquico'].label = labels['hierarquico']
            self.fields['departamento_destino'].label = labels['departamento']
            self.fields['seccao_destino'].label = labels['seccao']
            
            # Sobrescrever labels para Governo Secretaria (layout 2x2)
            if self.is_governo_secretaria:
                self.fields['destino_hierarquico'].label = 'Governo / MAT'
                self.fields['destino_municipal'].label = 'Administração Municipal'
        else:
            self.fields['destino_hierarquico'].queryset = Administracao.objects.none()
            self.fields['destino_municipal'].queryset = Administracao.objects.none()
            self.fields['departamento_destino'].queryset = Departamento.objects.none()
            self.fields['seccao_destino'].queryset = Seccoes.objects.none()
            self.seccoes_fixas = False
            self.seccoes_data = None
            self.is_governo_secretaria = False

        self.fields['seccao_destino'].label_from_instance = lambda obj: obj.nome
        self.fields['destino_hierarquico'].label_from_instance = lambda obj: obj.nome
        self.fields['destino_municipal'].label_from_instance = lambda obj: obj.nome

    def clean(self):
        cleaned_data = super().clean()
        dest_hierarquico = cleaned_data.get('destino_hierarquico')
        dest_municipal = cleaned_data.get('destino_municipal')
        dept_destino = cleaned_data.get('departamento_destino')
        sec_destino = cleaned_data.get('seccao_destino')
        tipo_mov = cleaned_data.get('tipo_movimentacao')

        if tipo_mov == 'encaminhamento':
            # Contar quantos destinos foram selecionados
            selecionados = [d for d in [dest_hierarquico, dest_municipal, dept_destino, sec_destino] if d]
            
            if len(selecionados) == 0:
                raise ValidationError('Selecione um destino (Governo, Administração, Direção ou Secção).')
            
            if len(selecionados) > 1:
                raise ValidationError('Escolha APENAS UM destino.')

            # Se for destino hierárquico (Governo/MAT), validar e converter
            if dest_hierarquico:
                sec_geral = obter_secretaria_geral(dest_hierarquico)
                if not sec_geral:
                    raise ValidationError(f'A administração {dest_hierarquico.nome} não possui uma Secretaria Geral configurada para receber documentos.')
                cleaned_data['departamento_destino'] = sec_geral
            
            # Se for destino municipal, validar e converter da mesma forma
            if dest_municipal:
                sec_geral = obter_secretaria_geral(dest_municipal)
                if not sec_geral:
                    raise ValidationError(f'A administração {dest_municipal.nome} não possui uma Secretaria Geral configurada para receber documentos.')
                cleaned_data['departamento_destino'] = sec_geral
            
        return cleaned_data


# ===========================================================================
# CustomUserCreationForm (REFATORADO COM HierarchyManager)
# ===========================================================================

class CustomUserCreationForm(UserCreationForm):
    """
    Formulário customizado para criação de usuários.
    
    Usa HierarchyManager para carregar departamentos e secções
    de forma consistente com encaminhamento.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        label='Nome'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        label='Sobrenome'
    )

    telefone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )

    administracao = forms.ModelChoiceField(
        queryset=Administracao.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Administração'
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento'}),
        required=True,
        label='Departamento'
    )

    seccao = forms.ModelChoiceField(
        queryset=Seccoes.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_seccao'}),
        required=False,
        label='Secção (Opcional)'
    )

    nivel_acesso = forms.ChoiceField(
        choices=CustomUser.NIVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nível de Acesso'
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'telefone', 'administracao', 'departamento', 'seccao',
            'nivel_acesso', 'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

        # Filtrar níveis de acesso pelo tipo de administração
        if self.admin_user and self.admin_user.administracao:
            tipo = self.admin_user.administracao.tipo_municipio
            self.fields['nivel_acesso'].choices = CustomUser.niveis_para_tipo(tipo)

        # Popular departamentos se administração estiver presente
        if 'administracao' in self.data:
            try:
                admin_id = int(self.data.get('administracao'))
                administracao = Administracao.objects.get(id=admin_id)
                self.fields['departamento'].queryset = (
                    Departamento.objects.para_administracao(administracao)
                    .order_by('nome')
                )
            except (ValueError, TypeError, Administracao.DoesNotExist):
                self.fields['departamento'].queryset = Departamento.objects.none()
        elif self.instance.pk and self.instance.administracao:
            self.fields['departamento'].queryset = (
                Departamento.objects.para_administracao(self.instance.administracao)
                .order_by('nome')
            )

        # Popular secções se departamento estiver presente
        if 'departamento' in self.data:
            try:
                dept_id = int(self.data.get('departamento'))
                self.fields['seccao'].queryset = (
                    Seccoes.objects.filter(departamento_id=dept_id)
                    .order_by('nome')
                )
                
                # Validação adicional: secção deve pertencer à administração
                if 'administracao' in self.data:
                    admin_id = int(self.data.get('administracao'))
                    self.fields['seccao'].queryset = self.fields['seccao'].queryset.filter(
                        departamento__administracao_id=admin_id
                    )
            except (ValueError, TypeError):
                self.fields['seccao'].queryset = Seccoes.objects.none()
        elif self.instance.pk and self.instance.departamento:
            self.fields['seccao'].queryset = (
                Seccoes.objects.filter(departamento=self.instance.departamento)
                .order_by('nome')
            )

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        seccao = cleaned_data.get('seccao')

        # Se ambos forem selecionados, prioriza a secção e "esquece" o departamento
        if departamento and seccao:
            cleaned_data['departamento'] = None
        
        return cleaned_data


# ===========================================================================
# CriarUsuarioAdminForm (REFATORADO COM HierarchyManager)
# ===========================================================================

class CriarUsuarioAdminForm(UserCreationForm):
    """
    Formulário para admin_sistema criar usuários da sua administração.
    
    A administração é automaticamente a do admin logado (não aparece no form).
    Usa HierarchyManager para garantir consistência de hierarquia.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@exemplo.com'
        }),
        required=True
    )

    first_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nome'
        }),
        required=True,
        label='Nome'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Sobrenome'
        }),
        required=True,
        label='Sobrenome'
    )

    telefone = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+244 9XX XXX XXX'
        }),
        required=False
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_departamento'
        }),
        required=True,
        label='Departamento'
    )

    seccao = forms.ModelChoiceField(
        queryset=Seccoes.objects.none(),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'id_seccao'
        }),
        required=False,
        label='Secção (Opcional)'
    )

    nivel_acesso = forms.ChoiceField(
        choices=CustomUser.NIVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nível de Acesso'
    )

    class Meta:
        model = CustomUser
        fields = (
            'username', 'email', 'first_name', 'last_name',
            'telefone', 'departamento', 'seccao', 'nivel_acesso',
            'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Nome de usuário'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Senha'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirmar senha'
        })

        # Filtrar níveis de acesso pelo tipo de administração do admin logado
        if self.admin_user and self.admin_user.administracao:
            tipo = self.admin_user.administracao.tipo_municipio
            self.fields['nivel_acesso'].choices = CustomUser.niveis_para_tipo(tipo)

        # Filtrar departamentos pela administração do admin logado
        if self.admin_user and self.admin_user.administracao:
            self.fields['departamento'].queryset = (
                Departamento.objects.filter(
                    administracao=self.admin_user.administracao
                )
                .order_by('nome')
            )

        # Popular secções se departamento foi selecionado
        if 'departamento' in self.data:
            try:
                dept_id = int(self.data.get('departamento'))
                self.fields['seccao'].queryset = (
                    Seccoes.objects.filter(
                        departamento_id=dept_id,
                        departamento__administracao=self.admin_user.administracao
                    )
                    .order_by('nome')
                )
            except (ValueError, TypeError, AttributeError):
                self.fields['seccao'].queryset = Seccoes.objects.none()
        elif self.instance.pk and self.instance.departamento:
            self.fields['seccao'].queryset = (
                Seccoes.objects.filter(departamento=self.instance.departamento)
                .order_by('nome')
            )

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        seccao = cleaned_data.get('seccao')

        # Se ambos forem selecionados, prioriza a secção e "esquece" o departamento
        if departamento and seccao:
            cleaned_data['departamento'] = None
        
        return cleaned_data

    def _post_clean(self):
        """Define administração ANTES da validação do modelo."""
        if self.admin_user and self.admin_user.administracao:
            self.instance.administracao = self.admin_user.administracao
        super()._post_clean()

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.admin_user and self.admin_user.administracao:
            user.administracao = self.admin_user.administracao
        if commit:
            user.save()
        return user


# ===========================================================================
# Outros Formulários (Sem Mudanças Significativas)
# ===========================================================================

class DespachoForm(forms.Form):
    """Formulário para registrar despacho em documento."""
    
    STATUS_CHOICES = [
        ('', 'Manter status atual'),
        (StatusDocumento.APROVADO, 'Aprovar'),
        (StatusDocumento.REPROVADO, 'Rejeitar'),
        (StatusDocumento.ARQUIVADO, 'Arquivar'),
    ]

    despacho = forms.CharField(
        label='Despacho/Parecer',
        required=True,
        widget=TinyMCE(attrs={'cols': 80, 'rows': 5})
    )

    novo_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Alterar Status',
        required=False
    )

    observacoes = forms.CharField(label='Observações', required=False)


class BuscaAvancadaForm(forms.Form):
    """Formulário para busca avançada de documentos."""
    
    titulo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar no título'
        }),
        required=False
    )

    conteudo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar no conteúdo'
        }),
        required=False
    )

    numero_protocolo = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Número do protocolo'
        }),
        required=False
    )

    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Todos os tipos'
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Todos os departamentos'
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos')] + StatusDocumento.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    prioridade = forms.ChoiceField(
        choices=[('', 'Todas')] + Documento.PRIORIDADE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Data Início'
    )

    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Data Fim'
    )

    tags = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tags separadas por vírgula'
        }),
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user and self.user.administracao:
            self.fields['departamento'].queryset = (
                Departamento.objects.filter(
                    administracao=self.user.administracao,
                    ativo=True
                )
                .order_by('nome')
            )
        elif self.user and self.user.is_superuser:
            self.fields['departamento'].queryset = (
                Departamento.objects.filter(ativo=True)
                .order_by('nome')
            )
        else:
            self.fields['departamento'].queryset = Departamento.objects.none()


class DepartamentoForm(forms.ModelForm):
    """Formulário para departamentos."""

    class Meta:
        model = Departamento
        fields = ['nome', 'codigo', 'descricao', 'responsavel', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'responsavel': forms.Select(attrs={'class': 'form-select'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TipoDocumentoForm(forms.ModelForm):
    """Formulário para tipos de documento."""

    class Meta:
        model = TipoDocumento
        fields = ['nome', 'descricao', 'prazo_dias', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'prazo_dias': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AnexoForm(forms.ModelForm):
    """Formulário para anexos."""

    class Meta:
        model = Anexo
        fields = ['arquivo', 'nome', 'descricao']
        widgets = {
            'arquivo': forms.FileInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2
            }),
        }


class FiltroRelatorioForm(forms.Form):
    """Formulário para filtros de relatórios."""
    
    data_inicio = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Data Início'
    )

    data_fim = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False,
        label='Data Fim'
    )

    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Todos os departamentos'
    )

    tipo_documento = forms.ModelChoiceField(
        queryset=TipoDocumento.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False,
        empty_label='Todos os tipos'
    )

    status = forms.ChoiceField(
        choices=[('', 'Todos')] + StatusDocumento.choices,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )


class ArmazenamentoDocumentoForm(forms.ModelForm):
    """Formulário para registrar o armazenamento físico de documentos."""

    class Meta:
        model = ArmazenamentoDocumento
        fields = [
            'local_armazenamento',
            'estante', 'prateleira', 'dossie', 'caixa', 'posicao',
            'observacoes'
        ]
        widgets = {
            'local_armazenamento': forms.Select(attrs={
                'class': 'form-select',
            }),
            'estante': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: EST-01',
                'maxlength': '50',
            }),
            'prateleira': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: PRAT-A',
                'maxlength': '50',
            }),
            'dossie': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: DOS-001',
                'maxlength': '50',
            }),
            'caixa': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: CX-05 (opcional)',
                'maxlength': '50',
            }),
            'posicao': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Ex: Posição 3',
                'maxlength': '50',
            }),
            'observacoes': forms.Textarea(attrs={
                'class': 'form-textarea',
                'rows': 3,
                'placeholder': 'Observações sobre o armazenamento'
            }),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.documento = kwargs.pop('documento', None)
        super().__init__(*args, **kwargs)

        # Filtrar locais de armazenamento por departamento do usuário
        if self.user:
            departamento_usuario = None
            if hasattr(self.user, 'seccao') and self.user.seccao:
                departamento_usuario = self.user.seccao.departamento
            elif hasattr(self.user, 'departamento_efetivo'):
                departamento_usuario = self.user.departamento_efetivo

            if departamento_usuario:
                self.fields['local_armazenamento'].queryset = (
                    LocalArmazenamento.objects.filter(
                        departamento=departamento_usuario,
                        ativo=True
                    )
                    .order_by('tipo', 'codigo')
                )
            else:
                self.fields['local_armazenamento'].queryset = LocalArmazenamento.objects.none()
        else:
            self.fields['local_armazenamento'].queryset = LocalArmazenamento.objects.filter(ativo=True)

        # Campos não obrigatórios
        self.fields['local_armazenamento'].required = False
        self.fields['estante'].required = False
        self.fields['prateleira'].required = False
        self.fields['dossie'].required = False
        self.fields['caixa'].required = False
        self.fields['posicao'].required = False

    def clean(self):
        cleaned_data = super().clean()
        local_cadastrado = cleaned_data.get('local_armazenamento')
        estante = cleaned_data.get('estante')
        prateleira = cleaned_data.get('prateleira')
        dossie = cleaned_data.get('dossie')
        caixa = cleaned_data.get('caixa')

        tem_local_cadastrado = local_cadastrado is not None
        tem_local_manual = any([estante, prateleira, dossie, caixa])

        if not tem_local_cadastrado and not tem_local_manual:
            raise ValidationError(
                'Deve informar um local de armazenamento cadastrado OU '
                'preencher os campos manuais (pelo menos estante, prateleira ou dossiê).'
            )

        return cleaned_data


# ===========================================================================
# EditarUsuarioAdminForm (NOVO para Edição)
# ===========================================================================

class EditarUsuarioAdminForm(forms.ModelForm):
    """
    Formulário para editar usuários existentes.
    Permite alterar nome, email, departamento, secção e nível de acesso.
    Não permite alterar senha aqui (usar fluxo de reset ou outro form se necessário).
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        required=True
    )
    
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        label='Nome'
    )

    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=True,
        label='Sobrenome'
    )
    
    telefone = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        required=False
    )
    
    departamento = forms.ModelChoiceField(
        queryset=Departamento.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_departamento_edit'}),
        required=True,
        label='Departamento'
    )

    seccao = forms.ModelChoiceField(
        queryset=Seccoes.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_seccao_edit'}),
        required=False,
        label='Secção (Opcional)'
    )

    nivel_acesso = forms.ChoiceField(
        choices=CustomUser.NIVEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        label='Nível de Acesso'
    )
    
    is_active = forms.BooleanField(
        required=False, 
        label='Usuário Ativo',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = CustomUser
        fields = (
            'email', 'first_name', 'last_name', 'telefone', 
            'departamento', 'seccao', 'nivel_acesso', 'is_active'
        )

    def __init__(self, *args, **kwargs):
        self.admin_user = kwargs.pop('admin_user', None)
        super().__init__(*args, **kwargs)
        
        # 1. Filtrar Departamento pela Administração do Admin Logado
        if self.admin_user and self.admin_user.administracao:
            admin_user_admin = self.admin_user.administracao
            
            # Popular Depto Queryset
            self.fields['departamento'].queryset = (
                Departamento.objects.filter(
                    administracao=admin_user_admin
                )
                .order_by('nome')
            )
            
            # Popular Nivel Acesso Choices
            tipo = admin_user_admin.tipo_municipio
            self.fields['nivel_acesso'].choices = CustomUser.niveis_para_tipo(tipo)
        else:
             self.fields['departamento'].queryset = Departamento.objects.none()

        # 2. Filtrar Secção (Lógica de Dependência)
        dept_id = None
        
        # Tenta pegar do POST (bind)
        if self.data and 'departamento' in self.data:
            try:
                dept_id = int(self.data.get('departamento'))
            except (ValueError, TypeError):
                pass
        # Se não tem POST, pega da instância (initial)
        elif self.instance.pk and self.instance.departamento:
            dept_id = self.instance.departamento.id
            
            # Caso especial: Se usuário tem secção e departamento, o campo departamento no form
            # pode vir vazio na limpeza (clean), mas na inicialização queremos ver o departamento pai
            if not dept_id and self.instance.seccao and self.instance.seccao.departamento:
                 dept_id = self.instance.seccao.departamento.id
                 self.initial['departamento'] = dept_id

        # Popular Queryset de Secção
        if dept_id:
             try:
                self.fields['seccao'].queryset = (
                    Seccoes.objects.filter(
                        departamento_id=dept_id,
                        # Garante isolamento: Secção deve ser da mesma administração
                        departamento__administracao=self.admin_user.administracao if self.admin_user else None
                    )
                    .order_by('nome')
                )
             except (AttributeError, ValueError):
                self.fields['seccao'].queryset = Seccoes.objects.none()
        else:
             self.fields['seccao'].queryset = Seccoes.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        departamento = cleaned_data.get('departamento')
        seccao = cleaned_data.get('seccao')

        # Se Secção for selecionada, ela define o departamento "real" (propriedade do modelo)
        # O campo departamento pode ser ignorado ou setado para None dependendo da lógica do seu model.
        # SE seu model permite departamento=None quando tem seccao:
        if seccao:
            cleaned_data['departamento'] = None
        
        # Se NÃO tiver secção, Departamento é obrigatório
        if not seccao and not departamento:
             self.add_error('departamento', 'Selecione um departamento ou uma secção.')
        
        return cleaned_data

class DistribuirDocumentoForm(forms.Form):
    """Formulário para chefia distribuir documento a um técnico."""
    
    tecnico = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Atribuir ao Técnico',
        required=True
    )
    
    observacoes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='Instruções / Observações',
        required=False
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if self.user:
            # Filtrar técnicos do mesmo setor que o usuário (Chefe)
            ctx = _get_contexto_usuario(self.user)
            dept = ctx['dept']
            seccao = ctx['seccao']
            
            qs = CustomUser.objects.filter(is_active=True).exclude(pk=self.user.pk)
            
            if seccao:
                qs = qs.filter(seccao=seccao)
            elif dept:
                # Inclui usuários DIRETOS do departamento OU usuários das SECÇÕES desse departamento
                from django.db.models import Q
                qs = qs.filter(Q(departamento=dept) | Q(seccao__departamento=dept))
                
            self.fields['tecnico'].queryset = qs.order_by('first_name')
            self.fields['tecnico'].label_from_instance = lambda u: f"{u.get_full_name()} ({u.username})"

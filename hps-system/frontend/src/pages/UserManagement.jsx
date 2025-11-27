// Página de Gestión de Usuarios del Sistema HPS
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { userService, teamService } from '../services/apiService';
import hpsService from '../services/hpsService';
import useAuthStore from '../store/authStore';
import { formatErrorForDisplay } from '../utils/errorHandler';
import {
  PlusIcon,
  PencilIcon,
  TrashIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  LinkIcon,
  ArrowLeftIcon,
  ArrowPathIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';
import PermanentDeleteModal from '../components/PermanentDeleteModal';

// Función helper para obtener colores de roles (consistente con Dashboard)
const getRoleColors = (role) => {
  const roleColors = {
    'admin': 'bg-red-100 text-red-800',             // Rojo (Dashboard: bg-red-500)
    'jefe_seguridad': 'bg-orange-100 text-orange-800', // Naranja (Dashboard: bg-orange-500)
    'jefe_seguridad_suplente': 'bg-orange-100 text-orange-800', // Naranja (mismo que jefe_seguridad)
    'crypto': 'bg-yellow-100 text-yellow-800',     // Amarillo (Dashboard: bg-yellow-500)
    'team_lead': 'bg-blue-100 text-blue-800',      // Azul (Dashboard: bg-blue-500)
    'member': 'bg-green-100 text-green-800'        // Verde (Dashboard: bg-green-500)
  };
  return roleColors[role] || 'bg-gray-100 text-gray-800';
};

// Función helper para obtener etiquetas de roles
const getRoleLabel = (role) => {
  const roleLabels = {
    'admin': 'Admin',
    'jefe_seguridad': 'Jefe Seguridad',
    'jefe_seguridad_suplente': 'Jefe Seguridad Suplente',
    'crypto': 'Crypto',
    'team_lead': 'Líder Equipo',
    'member': 'Miembro'
  };
  return roleLabels[role] || role?.replace('_', ' ');
};

// Función helper para ordenar usuarios por jerarquía de roles
const sortUsersByRole = (users) => {
  const roleOrder = {
    'admin': 1,
    'jefe_seguridad': 2,
    'jefe_seguridad_suplente': 3,
    'crypto': 4,
    'team_lead': 5,
    'member': 6
  };
  
  return users.sort((a, b) => {
    const roleA = roleOrder[a.role] || 999;
    const roleB = roleOrder[b.role] || 999;
    
    // Si tienen el mismo rol, ordenar alfabéticamente por nombre
    if (roleA === roleB) {
      return a.full_name.localeCompare(b.full_name);
    }
    
    return roleA - roleB;
  });
};

const UserManagement = () => {
  const navigate = useNavigate();
  const { canManageUsers } = useAuthStore();
  const [users, setUsers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showViewModal, setShowViewModal] = useState(false);
  const [showTokenModal, setShowTokenModal] = useState(false);
  const [generatedToken, setGeneratedToken] = useState(null);
  const [tokenLoading, setTokenLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showInactiveUsers, setShowInactiveUsers] = useState(false);
  const [activeTab, setActiveTab] = useState('users'); // 'users' o 'teams'
  const [formData, setFormData] = useState({
    email: '',
    full_name: '',
    password: '',
    role: 'member',
    team_id: 'd8574c01-851f-4716-9ac9-bbda45469bdf' // AICOX por defecto
  });
  
  // Estados para gestión de equipos
  const [teamFormData, setTeamFormData] = useState({
    name: '',
    description: '',
    team_lead_id: ''
  });
  const [showCreateTeamModal, setShowCreateTeamModal] = useState(false);
  const [showEditTeamModal, setShowEditTeamModal] = useState(false);
  const [showViewTeamModal, setShowViewTeamModal] = useState(false);
  const [selectedTeam, setSelectedTeam] = useState(null);
  const [availableLeaders, setAvailableLeaders] = useState([]);
  const [teamStats, setTeamStats] = useState(null);
  
  // Estados para modales de confirmación
  const [showDeleteConfirmModal, setShowDeleteConfirmModal] = useState(false);
  const [showActivateConfirmModal, setShowActivateConfirmModal] = useState(false);
  const [showPermanentDeleteModal, setShowPermanentDeleteModal] = useState(false);
  const [userToDelete, setUserToDelete] = useState(null);
  const [userToActivate, setUserToActivate] = useState(null);
  const [userToPermanentDelete, setUserToPermanentDelete] = useState(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [activateLoading, setActivateLoading] = useState(false);
  const [permanentDeleteLoading, setPermanentDeleteLoading] = useState(false);
  
  // Estados para paginación
  const [currentPage, setCurrentPage] = useState(1);
  const [usersPerPage] = useState(25);

  // Verificar permisos
  useEffect(() => {
    if (!canManageUsers()) {
      navigate('/dashboard');
      return;
    }
    loadUsers();
    loadTeams();
    loadTeamStats();
    loadAvailableLeaders();
  }, [canManageUsers, navigate]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const response = await userService.getUsers();
      console.log('🔍 Datos recibidos del backend:', response);
      // Cargar todos los usuarios, el filtrado se hace en el render
      setUsers(response.users || []);
    } catch (error) {
      console.error('Error cargando usuarios:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadTeams = async () => {
    try {
      const response = await teamService.getTeams();
      const teamsList = response.teams || [];
      setTeams(teamsList);
      
      // Actualizar la lista de equipos disponibles para usuarios
      // Asegurar que AICOX esté siempre disponible
      const aicoxTeam = teamsList.find(team => team.name === 'AICOX');
      if (!aicoxTeam) {
        teamsList.unshift({
          id: 'd8574c01-851f-4716-9ac9-bbda45469bdf',
          name: 'AICOX',
          description: 'Equipo genérico'
        });
      }
      
      console.log('Equipos cargados:', teamsList);
    } catch (error) {
      console.error('Error cargando equipos:', error);
      // Fallback al equipo AICOX estático si falla la API
      const fallbackTeams = [
        { id: 'd8574c01-851f-4716-9ac9-bbda45469bdf', name: 'AICOX', description: 'Equipo genérico' }
      ];
      setTeams(fallbackTeams);
    }
  };

  const loadTeamStats = async () => {
    try {
      const response = await teamService.getTeamStats();
      setTeamStats(response);
    } catch (error) {
      console.error('Error cargando estadísticas de equipos:', error);
    }
  };

  const loadAvailableLeaders = async (teamId = null) => {
    try {
      if (teamId) {
        // Cargar miembros del equipo específico
        const response = await teamService.getTeamMembers(teamId);
        setAvailableLeaders(response);
      } else {
        // Cargar líderes disponibles para crear equipos
        const response = await teamService.getAvailableLeaders();
        setAvailableLeaders(response);
      }
    } catch (error) {
      console.error('Error cargando líderes disponibles:', error);
    }
  };

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      // El backend se encarga de asignar automáticamente al equipo AICOX si team_id es null
      const userData = {
        ...formData
        // No necesitamos modificar team_id aquí, el backend lo maneja
      };
      
      await userService.createUser(userData);
      setShowCreateModal(false);
      setFormData({ 
        email: '', 
        full_name: '', 
        password: '', 
        role: 'member', 
        team_id: 'd8574c01-851f-4716-9ac9-bbda45469bdf' // AICOX por defecto
      });
      loadUsers();
    } catch (error) {
      console.error('Error creando usuario:', error);
      const errorMessage = formatErrorForDisplay(error.response?.data || error);
      alert('Error al crear usuario: ' + errorMessage);
    }
  };

  const handleEditUser = async (e) => {
    e.preventDefault();
    try {
      // Asegurar que el rol siempre sea un string, no un objeto
      const updateData = {
        ...formData,
        role: typeof formData.role === 'string' ? formData.role : (formData.role?.name || formData.role || 'member')
      };
      
      await userService.updateUser(selectedUser.id, updateData);
      setShowEditModal(false);
      setSelectedUser(null);
      setFormData({ email: '', full_name: '', password: '', role: 'member', team_id: 'd8574c01-851f-4716-9ac9-bbda45469bdf' });
      loadUsers();
    } catch (error) {
      console.error('Error actualizando usuario:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          error.message || 
                          'Error desconocido al actualizar usuario';
      alert('Error al actualizar usuario: ' + errorMessage);
    }
  };

  const openDeleteConfirmModal = (user) => {
    setUserToDelete(user);
    setShowDeleteConfirmModal(true);
  };

  const handleDeleteUser = async () => {
    if (!userToDelete) return;
    
    setDeleteLoading(true);
    try {
      console.log('Eliminando usuario:', userToDelete.id);
      const result = await userService.deleteUser(userToDelete.id);
      console.log('Resultado de eliminación:', result);
      
      // Cerrar modal y recargar usuarios
      setShowDeleteConfirmModal(false);
      setUserToDelete(null);
      loadUsers();
    } catch (error) {
      console.error('Error eliminando usuario:', error);
      // El error se mostrará en el modal
    } finally {
      setDeleteLoading(false);
    }
  };

  const openActivateConfirmModal = (user) => {
    setUserToActivate(user);
    setShowActivateConfirmModal(true);
  };

  const handleActivateUser = async () => {
    if (!userToActivate) return;
    
    setActivateLoading(true);
    try {
      console.log('Activando usuario:', userToActivate.id);
      const result = await userService.activateUser(userToActivate.id);
      console.log('Resultado de activación:', result);
      
      // Cerrar modal y recargar usuarios
      setShowActivateConfirmModal(false);
      setUserToActivate(null);
      loadUsers();
    } catch (error) {
      console.error('Error activando usuario:', error);
      // El error se mostrará en el modal
    } finally {
      setActivateLoading(false);
    }
  };

  const openPermanentDeleteConfirmModal = (user) => {
    setUserToPermanentDelete(user);
    setShowPermanentDeleteModal(true);
  };

  const handlePermanentDeleteUser = async () => {
    if (!userToPermanentDelete) return;
    
    setPermanentDeleteLoading(true);
    try {
      console.log('Eliminando usuario definitivamente:', userToPermanentDelete.id);
      const result = await userService.permanentlyDeleteUser(userToPermanentDelete.id);
      console.log('Resultado de eliminación definitiva:', result);
      
      // Cerrar modal y recargar usuarios
      setShowPermanentDeleteModal(false);
      setUserToPermanentDelete(null);
      loadUsers();
      
      alert('Usuario eliminado definitivamente de la base de datos');
    } catch (error) {
      console.error('Error eliminando usuario definitivamente:', error);
      const errorMessage = formatErrorForDisplay(error.response?.data || error);
      alert('Error al eliminar usuario definitivamente: ' + errorMessage);
    } finally {
      setPermanentDeleteLoading(false);
    }
  };

  // Funciones para manejo de tokens HPS
  const openTokenModal = (user) => {
    setSelectedUser(user);
    setShowTokenModal(true);
    setGeneratedToken(null);
  };

  const createHPSToken = async () => {
    if (!selectedUser) return;
    
    setTokenLoading(true);
    try {
      const tokenData = {
        email: selectedUser.email,
        purpose: `Solicitud HPS para ${selectedUser.first_name} ${selectedUser.last_name}`,
        hours_valid: 72
      };

      const result = await hpsService.createToken(tokenData);
      
      console.log('Token result:', result);
      console.log('Token result data:', result.data);
      
      if (result.success) {
        setGeneratedToken(result.data);
        console.log('Generated token set:', result.data);
      } else {
        alert('Error al crear token: ' + result.error);
      }
    } catch (error) {
      console.error('Error creating HPS token:', error);
      alert('Error al crear el token HPS');
    } finally {
      setTokenLoading(false);
    }
  };

  const copyTokenUrlToClipboard = (url) => {
    navigator.clipboard.writeText(url).then(() => {
      alert('URL copiada al portapapeles');
    }).catch(() => {
      // Fallback para navegadores que no soportan clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = url;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      alert('URL copiada al portapapeles');
    });
  };

  // Función para generar nombre completo automáticamente desde el email
  const generateFullNameFromEmail = (email) => {
    if (!email) return '';
    const emailPart = email.split('@')[0];
    // Capitalizar primera letra y convertir guiones bajos/guiones a espacios
    return emailPart
      .replace(/[_-]/g, ' ')
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };

  // Funciones para gestión de equipos
  const handleCreateTeam = async (e) => {
    e.preventDefault();
    try {
      // Limpiar datos antes de enviar
      const cleanData = {
        name: teamFormData.name,
        description: teamFormData.description || null,
        team_lead_id: teamFormData.team_lead_id || null
      };
      
      console.log('Datos a enviar:', cleanData);
      
      await teamService.createTeam(cleanData);
      setShowCreateTeamModal(false);
      setTeamFormData({ name: '', description: '', team_lead_id: '' });
      
      // Recargar equipos, estadísticas y usuarios (por si cambió el rol de algún usuario)
      await loadTeams();
      await loadTeamStats();
      await loadUsers();
      
      // Mostrar mensaje de éxito
      alert('Equipo creado exitosamente');
    } catch (error) {
      console.error('Error creando equipo:', error);
      const errorMessage = formatErrorForDisplay(error.response?.data || error);
      alert('Error al crear equipo: ' + errorMessage);
    }
  };

  const handleEditTeam = async (e) => {
    e.preventDefault();
    try {
      // Limpiar datos antes de enviar
      const cleanData = {
        name: teamFormData.name,
        description: teamFormData.description || null,
        team_lead_id: teamFormData.team_lead_id || null
      };
      
      console.log('Datos a enviar:', cleanData);
      
      await teamService.updateTeam(selectedTeam.id, cleanData);
      setShowEditTeamModal(false);
      setTeamFormData({ name: '', description: '', team_lead_id: '' });
      
      // Recargar equipos, estadísticas y usuarios (por si cambió el rol de algún usuario)
      await loadTeams();
      await loadTeamStats();
      await loadUsers();
      
      // Mostrar mensaje de éxito
      alert('Equipo actualizado exitosamente');
    } catch (error) {
      console.error('Error actualizando equipo:', error);
      const errorMessage = formatErrorForDisplay(error.response?.data || error);
      alert('Error al actualizar equipo: ' + errorMessage);
    }
  };

  const handleDeleteTeam = async (teamId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar este equipo?')) {
      return;
    }
    
    try {
      await teamService.deleteTeam(teamId);
      
      // Recargar equipos y estadísticas
      await loadTeams();
      await loadTeamStats();
      
      // Mostrar mensaje de éxito
      alert('Equipo eliminado exitosamente');
    } catch (error) {
      console.error('Error eliminando equipo:', error);
      const errorMessage = formatErrorForDisplay(error.response?.data || error);
      alert('Error al eliminar equipo: ' + errorMessage);
    }
  };

  const openCreateTeamModal = () => {
    setTeamFormData({ name: '', description: '', team_lead_id: '' });
    setShowCreateTeamModal(true);
  };

  const openEditTeamModal = (team) => {
    setSelectedTeam(team);
    setTeamFormData({
      name: team.name,
      description: team.description || '',
      team_lead_id: team.team_lead_id || ''
    });
    // Cargar líderes disponibles para este equipo específico
    loadAvailableLeaders(team.id);
    setShowEditTeamModal(true);
  };

  const openViewTeamModal = async (team) => {
    try {
      // Cargar detalles completos del equipo con miembros
      const teamDetail = await teamService.getTeamDetail(team.id);
      setSelectedTeam(teamDetail);
      setShowViewTeamModal(true);
    } catch (error) {
      console.error('Error cargando detalles del equipo:', error);
      // Fallback a la información básica si falla la carga
      setSelectedTeam(team);
      setShowViewTeamModal(true);
    }
  };

  const openEditModal = (user) => {
    setSelectedUser(user);
    setFormData({
      email: user.email,
      full_name: user.full_name || `${user.first_name || ''} ${user.last_name || ''}`.trim(),
      password: '',
      role: user.role?.name || user.role || 'member', // role puede venir como objeto {name: "rol"} o string
      team_id: user.team_id || 'd8574c01-851f-4716-9ac9-bbda45469bdf' // AICOX por defecto si no tiene equipo
    });
    setShowEditModal(true);
  };

  const openViewModal = (user) => {
    setSelectedUser(user);
    setShowViewModal(true);
  };


  const filteredUsers = sortUsersByRole(users.filter(user => {
    const matchesSearch = (user.email || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.first_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (user.last_name || '').toLowerCase().includes(searchTerm.toLowerCase());
    const matchesRole = roleFilter === 'all' || user.role === roleFilter;
    
    // Filtrar por estado de actividad
    const matchesActiveStatus = showInactiveUsers ? !user.is_active : user.is_active;
    
    return matchesSearch && matchesRole && matchesActiveStatus;
  }));

  // Lógica de paginación
  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
  const startIndex = (currentPage - 1) * usersPerPage;
  const endIndex = startIndex + usersPerPage;
  const paginatedUsers = filteredUsers.slice(startIndex, endIndex);

  // Resetear página cuando cambien los filtros
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, roleFilter, showInactiveUsers]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="w-full px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {activeTab === 'users' ? 'Gestión de Usuarios' : 'Gestión de Equipos'}
              </h1>
              <p className="text-sm text-gray-600">
                {activeTab === 'users' 
                  ? 'Administrar usuarios del sistema HPS' 
                  : 'Administrar equipos del sistema HPS'
                }
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <ArrowLeftIcon className="h-4 w-4 mr-2" />
                Volver al Dashboard
              </button>
              
              {activeTab === 'users' && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
                >
                  <PlusIcon className="h-5 w-5 mr-2" />
                  Nuevo Usuario
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Pestañas de navegación */}
        <div className="bg-white rounded-lg shadow mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('users')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'users'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                👥 Usuarios
              </button>
              <button
                onClick={() => setActiveTab('teams')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'teams'
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                🏢 Equipos
              </button>
            </nav>
          </div>
        </div>

        {/* Contenido de Usuarios */}
        {activeTab === 'users' && (
          <>
            {/* Filtros y búsqueda */}
            <div className="bg-white p-6 rounded-lg shadow mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <MagnifyingGlassIcon className="h-5 w-5 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Buscar usuarios..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <FunnelIcon className="h-5 w-5 text-gray-400" />
                <select
                  value={roleFilter}
                  onChange={(e) => setRoleFilter(e.target.value)}
                  className="border border-gray-300 rounded-md px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                >
                  <option value="all">Todos los roles</option>
                  <option value="admin">Administradores</option>
                  <option value="jefe_seguridad">Jefe de Seguridad</option>
                  <option value="jefe_seguridad_suplente">Jefe de Seguridad Suplente</option>
                  <option value="crypto">Crypto</option>
                  <option value="team_lead">Líderes de Equipo</option>
                  <option value="member">Miembros</option>
                </select>
              </div>
              
              <button
                onClick={() => setShowInactiveUsers(!showInactiveUsers)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
                  showInactiveUsers 
                    ? 'bg-orange-100 text-orange-700 border border-orange-300' 
                    : 'bg-gray-100 text-gray-700 border border-gray-300'
                }`}
              >
                {showInactiveUsers ? 'Ocultar Inactivos' : 'Mostrar Inactivos'}
              </button>
            </div>
          </div>
        </div>

        {/* Tabla de usuarios */}
        <div className="bg-white shadow rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Usuario
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Rol
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Equipo
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Estado
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    HPS
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Último Acceso
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Acciones
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedUsers.map((user) => (
                  <tr key={user.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                          <span className="text-white font-medium text-sm">
                            {user.full_name ? user.full_name.split(' ').map(n => n[0]).join('').slice(0, 2) : 'U'}
                          </span>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {user.full_name || 'Sin nombre'}
                          </div>
                          <div className="text-sm text-gray-500">
                            {user.email}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColors(user.role)}`}>
                        {getRoleLabel(user.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {user.team_name || user.team?.name || 'Sin equipo'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {user.is_active ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {user.hps_status === 'active' && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-green-100 text-green-800">
                          Activa
                          {user.hps_expires_at && (
                            <span className="ml-1 text-gray-500">
                              (hasta {new Date(user.hps_expires_at).toLocaleDateString('es-ES')})
                            </span>
                          )}
                        </span>
                      )}
                      {user.hps_status === 'pending' && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-yellow-100 text-yellow-800">
                          Pendiente ({user.pending_hps_requests})
                        </span>
                      )}
                      {user.hps_status === 'submitted' && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                          Enviada
                        </span>
                      )}
                      {user.hps_status === 'expired' && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-red-100 text-red-800">
                          Expirada
                          {user.hps_expires_at && (
                            <span className="ml-1 text-gray-500">
                              ({new Date(user.hps_expires_at).toLocaleDateString('es-ES')})
                            </span>
                          )}
                        </span>
                      )}
                      {user.hps_status === 'none' && (
                        <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 text-gray-800">
                          Sin HPS
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {user.last_login ? new Date(user.last_login).toLocaleDateString('es-ES') : 'Nunca'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex justify-end space-x-2">
                        <button
                          onClick={() => openViewModal(user)}
                          className="text-blue-600 hover:text-blue-900 p-1"
                          title="Ver detalles"
                        >
                          <EyeIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openTokenModal(user)}
                          className="text-green-600 hover:text-green-900 p-1"
                          title="Generar Token HPS"
                        >
                          <LinkIcon className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => openEditModal(user)}
                          className="text-indigo-600 hover:text-indigo-900 p-1"
                          title="Editar"
                        >
                          <PencilIcon className="h-4 w-4" />
                        </button>
                        {!user.is_active && (
                          <>
                            <button
                              onClick={() => openActivateConfirmModal(user)}
                              className="text-green-600 hover:text-green-900 p-1"
                              title="Activar usuario"
                            >
                              <ArrowPathIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => openPermanentDeleteConfirmModal(user)}
                              className="text-red-600 hover:text-red-900 p-1"
                              title="Eliminar definitivamente"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </>
                        )}
                        {user.is_active && (
                          <button
                            onClick={() => openDeleteConfirmModal(user)}
                            className="text-red-600 hover:text-red-900 p-1"
                            title="Marcar como inactivo"
                          >
                            <XMarkIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {filteredUsers.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-500 text-lg">No se encontraron usuarios</p>
            </div>
          )}
        </div>

        {/* Paginación */}
        {filteredUsers.length > 0 && totalPages > 1 && (
          <div className="bg-white px-4 py-3 flex items-center justify-between border-t border-gray-200 sm:px-6">
            <div className="flex-1 flex justify-between sm:hidden">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Anterior
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Siguiente
              </button>
            </div>
            <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
              <div>
                <p className="text-sm text-gray-700">
                  Mostrando <span className="font-medium">{startIndex + 1}</span> a{' '}
                  <span className="font-medium">{Math.min(endIndex, filteredUsers.length)}</span> de{' '}
                  <span className="font-medium">{filteredUsers.length}</span> resultados
                </p>
              </div>
              <div>
                <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Anterior</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                  
                  {/* Números de página */}
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`relative inline-flex items-center px-4 py-2 border text-sm font-medium ${
                          currentPage === pageNum
                            ? 'z-10 bg-blue-50 border-blue-500 text-blue-600'
                            : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <span className="sr-only">Siguiente</span>
                    <svg className="h-5 w-5" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                      <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                    </svg>
                  </button>
                </nav>
              </div>
            </div>
          </div>
        )}
          </>
        )}

        {/* Contenido de Equipos */}
        {activeTab === 'teams' && (
          <>
            {/* Estadísticas de equipos */}
            {teamStats && (
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-2 bg-blue-100 rounded-lg">
                      <span className="text-2xl">🏢</span>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Equipos</p>
                      <p className="text-2xl font-bold text-gray-900">{teamStats.total_teams}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-2 bg-green-100 rounded-lg">
                      <span className="text-2xl">✅</span>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Equipos Activos</p>
                      <p className="text-2xl font-bold text-gray-900">{teamStats.active_teams}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <span className="text-2xl">👥</span>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Total Miembros</p>
                      <p className="text-2xl font-bold text-gray-900">{teamStats.total_members}</p>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white p-6 rounded-lg shadow">
                  <div className="flex items-center">
                    <div className="p-2 bg-yellow-100 rounded-lg">
                      <span className="text-2xl">👑</span>
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Con Líderes</p>
                      <p className="text-2xl font-bold text-gray-900">{teamStats.teams_with_leaders}</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Lista de equipos */}
            <div className="bg-white shadow rounded-lg">
              <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                <h3 className="text-lg font-medium text-gray-900">Equipos</h3>
                <button
                  onClick={openCreateTeamModal}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
                >
                  <PlusIcon className="h-4 w-4 mr-2" />
                  Nuevo Equipo
                </button>
              </div>
              
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Equipo
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Descripción
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Líder
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Miembros
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Estado
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Acciones
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {teams.map((team) => (
                      <tr key={team.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">
                            {team.name}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 max-w-xs truncate">
                            {team.description || 'Sin descripción'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {team.team_lead_name || 'Sin líder'}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className="inline-flex px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                            {team.member_count} miembros
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                            team.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {team.is_active ? 'Activo' : 'Inactivo'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => openViewTeamModal(team)}
                              className="text-blue-600 hover:text-blue-900 p-1"
                              title="Ver detalles"
                            >
                              <EyeIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => openEditTeamModal(team)}
                              className="text-indigo-600 hover:text-indigo-900 p-1"
                              title="Editar"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            {team.is_active && (
                              <button
                                onClick={() => handleDeleteTeam(team.id)}
                                className="text-red-600 hover:text-red-900 p-1"
                                title="Eliminar"
                              >
                                <TrashIcon className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {teams.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-500 text-lg">No se encontraron equipos</p>
                </div>
              )}
            </div>
          </>
        )}
      </main>

      {/* Modal Crear Usuario */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Crear Nuevo Usuario</h3>
            </div>
            
            <form onSubmit={handleCreateUser} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => {
                    const email = e.target.value;
                    const fullName = generateFullNameFromEmail(email);
                    setFormData({
                      ...formData, 
                      email, 
                      full_name: fullName
                    });
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="usuario@ejemplo.com"
                  style={{ color: '#111827' }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  El email será tu nombre de usuario para acceder al sistema
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Completo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="Se genera automáticamente desde el email"
                  style={{ color: '#111827' }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  Se genera automáticamente desde tu email, pero puedes editarlo
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Contraseña
                </label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({...formData, password: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="Mínimo 6 caracteres"
                  style={{ color: '#111827' }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rol
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                >
                  <option value="admin">Administrador</option>
                  <option value="jefe_seguridad">Jefe de Seguridad</option>
                  <option value="jefe_seguridad_suplente">Jefe de Seguridad Suplente</option>
                  <option value="crypto">Crypto</option>
                  <option value="team_lead">Líder de Equipo</option>
                  <option value="member">Miembro</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Equipo
                </label>
                <select
                  value={formData.team_id || ''}
                  onChange={(e) => setFormData({...formData, team_id: e.target.value || null})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                >
                  <option value="">Sin equipo</option>
                  {teams.map((team) => (
                    <option key={team.id || 'none'} value={team.id || ''}>
                      {team.name} - {team.description}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  AICOX es el equipo por defecto. Selecciona otro equipo si es necesario.
                </p>
              </div>
            </form>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateUser}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Crear Usuario
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Editar Usuario */}
      {showEditModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Editar Usuario</h3>
            </div>
            
            <form onSubmit={handleEditUser} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  required
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                />
                <p className="text-xs text-gray-500 mt-1">
                  El email es tu nombre de usuario para acceder al sistema
                </p>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre Completo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={formData.full_name}
                  onChange={(e) => setFormData({...formData, full_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Rol
                </label>
                <select
                  value={formData.role}
                  onChange={(e) => setFormData({...formData, role: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                >
                  <option value="admin">Administrador</option>
                  <option value="jefe_seguridad">Jefe de Seguridad</option>
                  <option value="jefe_seguridad_suplente">Jefe de Seguridad Suplente</option>
                  <option value="crypto">Crypto</option>
                  <option value="team_lead">Líder de Equipo</option>
                  <option value="member">Miembro</option>
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Equipo
                </label>
                <select
                  value={formData.team_id || ''}
                  onChange={(e) => setFormData({...formData, team_id: e.target.value || null})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  style={{ color: '#111827' }}
                >
                  <option value="">Sin equipo</option>
                  {teams.map((team) => (
                    <option key={team.id || 'none'} value={team.id || ''}>
                      {team.name} - {team.description}
                    </option>
                  ))}
                </select>
                <p className="text-xs text-gray-500 mt-1">
                  AICOX es el equipo por defecto. Selecciona otro equipo si es necesario.
                </p>
              </div>
            </form>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => setShowEditModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={handleEditUser}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Actualizar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Ver Usuario */}
      {showViewModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-hidden">
            {/* Header con gradiente */}
            <div className="bg-gradient-to-r from-blue-600 to-indigo-700 px-8 py-6 text-white">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="h-16 w-16 rounded-full bg-white bg-opacity-20 flex items-center justify-center">
                    <span className="text-2xl font-bold text-white">
                      {selectedUser.full_name ? selectedUser.full_name.split(' ').map(n => n[0]).join('').slice(0, 2) : 'U'}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-2xl font-bold">{selectedUser.full_name || 'Sin nombre'}</h3>
                    <p className="text-blue-100 text-sm">{selectedUser.email}</p>
                  </div>
                </div>
                <button
                  onClick={() => setShowViewModal(false)}
                  className="text-white hover:text-gray-200 transition-colors p-2 rounded-full hover:bg-white hover:bg-opacity-20"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Contenido */}
            <div className="p-8">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Información básica */}
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">Información Básica</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Rol</p>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColors(selectedUser.role?.name || selectedUser.role)}`}>
                          {getRoleLabel(selectedUser.role?.name || selectedUser.role) || 'Sin rol'}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Equipo</p>
                        <p className="text-sm text-gray-900">{selectedUser.team_name || selectedUser.team?.name || 'Sin equipo'}</p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Estado</p>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          selectedUser.is_active 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-red-100 text-red-800'
                        }`}>
                          {selectedUser.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Información de actividad */}
                <div className="space-y-4">
                  <h4 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-2">Actividad</h4>
                  
                  <div className="space-y-3">
                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-orange-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Último Acceso</p>
                        <p className="text-sm text-gray-900">
                          {selectedUser.last_login ? new Date(selectedUser.last_login).toLocaleString('es-ES') : 'Nunca'}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center space-x-3">
                      <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center">
                        <svg className="w-4 h-4 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Fecha de Creación</p>
                        <p className="text-sm text-gray-900">
                          {new Date(selectedUser.created_at).toLocaleDateString('es-ES')}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 px-8 py-4 flex justify-end space-x-3">
              <button
                onClick={() => setShowViewModal(false)}
                className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Token HPS Seguro */}
      {showTokenModal && selectedUser && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] flex flex-col">
            <div className="px-6 py-4 border-b border-gray-200 flex-shrink-0">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">🔐 Generar Token HPS Seguro</h3>
                <button
                  onClick={() => {
                    setShowTokenModal(false);
                    setGeneratedToken(null);
                    setSelectedUser(null);
                  }}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                  title="Cerrar"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="px-6 py-4 flex-1 overflow-y-auto">
              <div className="space-y-6">
                {/* Información del usuario */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Usuario Destinatario
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {selectedUser.first_name} {selectedUser.last_name} ({selectedUser.email})
                  </p>
                </div>

                {/* Botón para generar token */}
                {!generatedToken && (
                  <div className="text-center">
                    <button
                      onClick={createHPSToken}
                      disabled={tokenLoading}
                      className="bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-md text-sm font-medium transition-colors"
                    >
                      {tokenLoading ? 'Generando Token Seguro...' : '🛡️ Generar Token Seguro'}
                    </button>
                  </div>
                )}

                {/* Token generado y URL */}
                {generatedToken && (
                  <>
                    <div className="bg-green-50 border border-green-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-green-800 mb-2">✅ Token Generado Exitosamente</h4>
                      <p className="text-xs text-green-700">
                        Válido hasta: {new Date(generatedToken.expires_at).toLocaleString()}
                      </p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        🔗 URL Segura del Formulario HPS
                      </label>
                      <div className="flex items-center space-x-2">
                        <input
                          type="text"
                          value={generatedToken.url}
                          readOnly
                          className="flex-1 p-3 border border-gray-300 rounded-md bg-gray-50 text-xs font-mono text-gray-700"
                        />
                        <button
                          onClick={() => copyTokenUrlToClipboard(generatedToken.url)}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-3 rounded-md text-sm font-medium transition-colors"
                        >
                          📋 Copiar
                        </button>
                      </div>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-blue-800 mb-2">🛡️ Características de Seguridad:</h4>
                      <ul className="text-sm text-blue-700 space-y-1">
                        <li>• <strong>Token único</strong>: Solo funciona una vez</li>
                        <li>• <strong>Expira automáticamente</strong>: en 72 horas</li>
                        <li>• <strong>Sin login requerido</strong>: para el usuario final</li>
                        <li>• <strong>Trazabilidad completa</strong>: registra quién solicitó el HPS</li>
                        <li>• <strong>HTTPS seguro</strong>: protección de datos en tránsito</li>
                      </ul>
                    </div>

                    <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
                      <h4 className="text-sm font-medium text-yellow-800 mb-2">📧 Instrucciones de Uso:</h4>
                      <ol className="text-sm text-yellow-700 space-y-1 list-decimal list-inside">
                        <li>Copia la URL usando el botón "Copiar"</li>
                        <li>Envía la URL al usuario por correo electrónico</li>
                        <li>El usuario completa el formulario sin necesidad de login</li>
                        <li>La solicitud aparecerá automáticamente en el sistema</li>
                        <li>El token se desactiva después del primer uso</li>
                      </ol>
                    </div>
                  </>
                )}
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3 flex-shrink-0 bg-white">
              {generatedToken && (
                <button
                  onClick={() => {
                    setShowTokenModal(false);
                    setGeneratedToken(null);
                    setSelectedUser(null);
                  }}
                  className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
                >
                  ✅ Completado
                </button>
              )}
              <button
                onClick={() => {
                  setShowTokenModal(false);
                  setGeneratedToken(null);
                  setSelectedUser(null);
                }}
                className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Crear Equipo */}
      {showCreateTeamModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Crear Nuevo Equipo</h3>
            </div>
            
            <form onSubmit={handleCreateTeam} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del Equipo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={teamFormData.name}
                  onChange={(e) => setTeamFormData({...teamFormData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="Nombre del equipo"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <textarea
                  value={teamFormData.description}
                  onChange={(e) => setTeamFormData({...teamFormData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  placeholder="Descripción del equipo"
                  rows={3}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Líder del Equipo (Seleccionar miembro)
                </label>
                <select
                  value={teamFormData.team_lead_id}
                  onChange={(e) => setTeamFormData({...teamFormData, team_lead_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  <option value="">Sin líder asignado</option>
                  {availableLeaders.map((leader) => (
                    <option key={leader.id} value={leader.id}>
                      {leader.full_name} ({leader.email}) - Rol: {leader.role}
                    </option>
                  ))}
                </select>
              </div>
            </form>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowCreateTeamModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={handleCreateTeam}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Crear Equipo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Editar Equipo */}
      {showEditTeamModal && selectedTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Editar Equipo</h3>
            </div>
            
            <form onSubmit={handleEditTeam} className="px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Nombre del Equipo <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={teamFormData.name}
                  onChange={(e) => setTeamFormData({...teamFormData, name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Descripción
                </label>
                <textarea
                  value={teamFormData.description}
                  onChange={(e) => setTeamFormData({...teamFormData, description: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                  rows={3}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Líder del Equipo (Seleccionar miembro)
                </label>
                <select
                  value={teamFormData.team_lead_id}
                  onChange={(e) => setTeamFormData({...teamFormData, team_lead_id: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-gray-900 bg-white"
                >
                  <option value="">Sin líder asignado</option>
                  {availableLeaders.map((leader) => (
                    <option key={leader.id} value={leader.id}>
                      {leader.full_name} ({leader.email}) - Rol: {leader.role}
                    </option>
                  ))}
                </select>
              </div>
            </form>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowEditTeamModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
              >
                Cancelar
              </button>
              <button
                onClick={handleEditTeam}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 border border-transparent rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Actualizar Equipo
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Ver Equipo */}
      {showViewTeamModal && selectedTeam && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Detalles del Equipo</h3>
            </div>
            
            <div className="px-6 py-4">
              <div className="space-y-6">
                {/* Información básica */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Nombre del Equipo
                    </label>
                    <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                      {selectedTeam.name}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Estado
                    </label>
                    <span className={`inline-flex px-3 py-1 text-sm font-semibold rounded-full ${
                      selectedTeam.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {selectedTeam.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Descripción
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {selectedTeam.description || 'Sin descripción'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Líder del Equipo
                  </label>
                  <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">
                    {selectedTeam.team_lead_name || 'Sin líder asignado'}
                  </p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Miembros del Equipo ({selectedTeam.members?.length || 0})
                  </label>
                  
                  {selectedTeam.members && selectedTeam.members.length > 0 ? (
                    <div className="bg-gray-50 p-4 rounded-md">
                      <div className="space-y-3">
                        {selectedTeam.members.map((member) => (
                          <div key={member.id} className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200">
                            <div className="flex-1">
                              <div className="flex items-center space-x-3">
                                <div className="flex-shrink-0">
                                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                                    <span className="text-sm font-medium text-blue-600">
                                      {member.full_name?.charAt(0) || member.email?.charAt(0) || '?'}
                                    </span>
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <p className="text-sm font-medium text-gray-900 truncate">
                                    {member.full_name || 'Sin nombre'}
                                  </p>
                                  <p className="text-sm text-gray-500 truncate">
                                    {member.email}
                                  </p>
                                </div>
                              </div>
                            </div>
                            <div className="flex-shrink-0">
                              <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColors(member.role)}`}>
                                {getRoleLabel(member.role)}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="bg-gray-50 p-4 rounded-md text-center">
                      <p className="text-sm text-gray-500">No hay miembros en este equipo</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setShowViewTeamModal(false)}
                className="px-6 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmación de Eliminación */}
      {showDeleteConfirmModal && userToDelete && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Marcar como Inactivo</h3>
            </div>
            
            <div className="px-6 py-4">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                  <XMarkIcon className="h-5 w-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">¿Marcar como inactivo?</p>
                  <p className="text-sm text-gray-500">{userToDelete.email}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">
                Esta acción marcará el usuario como inactivo. El usuario no podrá acceder al sistema 
                pero sus datos se mantendrán para futuras reactivaciones.
              </p>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowDeleteConfirmModal(false);
                  setUserToDelete(null);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                disabled={deleteLoading}
              >
                Cancelar
              </button>
              <button
                onClick={handleDeleteUser}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 disabled:opacity-50"
                disabled={deleteLoading}
              >
                {deleteLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Marcando como inactivo...
                  </div>
                ) : (
                  'Marcar como Inactivo'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Confirmación de Activación */}
      {showActivateConfirmModal && userToActivate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Confirmar Activación</h3>
            </div>
            
            <div className="px-6 py-4">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <ArrowPathIcon className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900">¿Activar usuario?</p>
                  <p className="text-sm text-gray-500">{userToActivate.email}</p>
                </div>
              </div>
              
              <p className="text-sm text-gray-600 mb-4">
                Esta acción reactivará el usuario y le permitirá acceder al sistema nuevamente.
              </p>
            </div>
            
            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setShowActivateConfirmModal(false);
                  setUserToActivate(null);
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 border border-gray-300 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
                disabled={activateLoading}
              >
                Cancelar
              </button>
              <button
                onClick={handleActivateUser}
                className="px-4 py-2 text-sm font-medium text-white bg-green-600 border border-transparent rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500 disabled:opacity-50"
                disabled={activateLoading}
              >
                {activateLoading ? (
                  <div className="flex items-center">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Activando...
                  </div>
                ) : (
                  'Activar Usuario'
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Eliminación Definitiva */}
      <PermanentDeleteModal
        isOpen={showPermanentDeleteModal}
        onClose={() => {
          setShowPermanentDeleteModal(false);
          setUserToPermanentDelete(null);
        }}
        onConfirm={handlePermanentDeleteUser}
        userEmail={userToPermanentDelete?.email || ''}
        loading={permanentDeleteLoading}
      />
    </div>
  );
};

export default UserManagement;

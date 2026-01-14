// Gestión de Equipo para Líderes de Equipo
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  ArrowLeftIcon, 
  PlusIcon, 
  PencilIcon, 
  TrashIcon,
  UserGroupIcon
} from '@heroicons/react/24/outline';
import useAuthStore from '../store/authStore';
import { userService } from '../services/apiService';
import { formatErrorForDisplay } from '../utils/errorHandler';

const TeamManagement = () => {
  const navigate = useNavigate();
  const { user, isTeamLeader } = useAuthStore();
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [roleFilter, setRoleFilter] = useState('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  useEffect(() => {
    if (!isTeamLeader()) {
      navigate('/unauthorized');
      return;
    }
    loadTeamData();
  }, [isTeamLeader, navigate]);

  const loadTeamData = async () => {
    try {
      setLoading(true);
      setError(null);

      console.log('TeamManagement - User:', user);
      console.log('TeamManagement - Team ID:', user?.team_id);

      if (!user?.team_id) {
        setError('No tienes un equipo asignado. Contacta al administrador.');
        return;
      }

      // Cargar miembros del equipo
      console.log('Cargando miembros del equipo:', user.team_id);
      const membersResult = await userService.getTeamMembers(user.team_id);
      console.log('Resultado miembros:', membersResult);
      if (membersResult.success) {
        setTeamMembers(membersResult.data);
      } else {
        setError('Error cargando miembros: ' + membersResult.error);
      }
    } catch (err) {
      console.error('Error cargando datos del equipo:', err);
      const errorMsg = formatErrorForDisplay(err);
      setError('Error cargando datos del equipo: ' + errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateUser = async (userData) => {
    try {
      const result = await userService.createUser({
        ...userData,
        team_id: user.team_id // Asignar al equipo del líder
      });
      
      if (result.success) {
        await loadTeamData();
        setShowCreateModal(false);
      } else {
        setError(result.error || 'Error creando usuario');
      }
    } catch (err) {
      console.error('Error creando usuario:', err);
      setError('Error creando usuario');
    }
  };

  const handleEditUser = async (userId, userData) => {
    try {
      const result = await userService.updateUser(userId, userData);
      
      if (result.success) {
        await loadTeamData();
        setShowEditModal(false);
        setSelectedUser(null);
      } else {
        setError(result.error || 'Error actualizando usuario');
      }
    } catch (err) {
      console.error('Error actualizando usuario:', err);
      setError('Error actualizando usuario');
    }
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('¿Estás seguro de que quieres eliminar este usuario?')) {
      return;
    }

    try {
      const result = await userService.deleteUser(userId);
      
      if (result.success) {
        await loadTeamData();
      } else {
        setError(result.error || 'Error eliminando usuario');
      }
    } catch (err) {
      console.error('Error eliminando usuario:', err);
      setError('Error eliminando usuario');
    }
  };

  // Función helper para obtener colores de roles (consistente con UserManagement)
  const getRoleColors = (role) => {
    const roleColors = {
      'admin': 'bg-red-100 text-red-800',
      'jefe_seguridad': 'bg-orange-100 text-orange-800',
      'jefe_seguridad_suplente': 'bg-orange-100 text-orange-800',
      'crypto': 'bg-yellow-100 text-yellow-800',
      'team_lead': 'bg-blue-100 text-blue-800',
      'member': 'bg-green-100 text-green-800'
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
        const nameA = (a.first_name + ' ' + a.last_name).trim() || a.email || '';
        const nameB = (b.first_name + ' ' + b.last_name).trim() || b.email || '';
        return nameA.localeCompare(nameB);
      }
      
      return roleA - roleB;
    });
  };

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
                Gestión de Mi Equipo
              </h1>
              <p className="text-sm text-gray-600">
                Administrar miembros de tu equipo
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
              
              <button
                onClick={() => setShowCreateModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium transition-colors flex items-center"
              >
                <PlusIcon className="h-5 w-5 mr-2" />
                Nuevo Miembro
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="w-full px-4 sm:px-6 lg:px-8 py-8">
        {/* Estadísticas del Equipo */}
        <div className="mb-8">
          <div className="grid grid-cols-1 md:grid-cols-1 gap-6">
            <div className="bg-white overflow-hidden shadow rounded-lg">
              <div className="p-5">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <UserGroupIcon className="h-6 w-6 text-gray-400" />
                  </div>
                  <div className="ml-5 w-0 flex-1">
                    <dl>
                      <dt className="text-sm font-medium text-gray-500 truncate">
                        Miembros del Equipo
                      </dt>
                      <dd className="text-lg font-medium text-gray-900">
                        {teamMembers.length}
                      </dd>
                    </dl>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Contenido de Miembros */}
        <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">
                Miembros del Equipo ({teamMembers.length})
              </h3>
              <div className="flex items-center space-x-4">
                <label className="text-sm font-medium text-gray-700">
                  Filtrar por rol:
                </label>
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
                  <option value="team_lead">Líder Equipo</option>
                  <option value="member">Miembros</option>
                </select>
              </div>
            </div>
            
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
                      Estado
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Acciones
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {sortUsersByRole([...teamMembers].filter(member => {
                    return roleFilter === 'all' || member.role === roleFilter;
                  })).map((member) => (
                    <tr key={member.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                            <span className="text-white font-medium text-sm">
                              {(() => {
                                const fullName = `${member.first_name || ''} ${member.last_name || ''}`.trim();
                                if (fullName) {
                                  return fullName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase();
                                }
                                return (member.email?.charAt(0) || 'U').toUpperCase();
                              })()}
                            </span>
                          </div>
                          <div className="ml-4">
                            <div className="text-sm font-medium text-gray-900">
                              {member.first_name && member.last_name 
                                ? `${member.first_name} ${member.last_name}`
                                : member.full_name || 'Sin nombre'}
                            </div>
                            <div className="text-sm text-gray-500">
                              {member.email}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getRoleColors(member.role)}`}>
                          {getRoleLabel(member.role)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          member.is_active !== false ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {member.is_active !== false ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        {member.role === 'member' && (
                          <div className="flex justify-end space-x-2">
                            <button
                              onClick={() => {
                                setSelectedUser(member);
                                setShowEditModal(true);
                              }}
                              className="text-blue-600 hover:text-blue-900"
                            >
                              <PencilIcon className="h-4 w-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteUser(member.id)}
                              className="text-red-600 hover:text-red-900"
                            >
                              <TrashIcon className="h-4 w-4" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

        {/* Modales */}
        {showCreateModal && (
          <CreateUserModal
            onClose={() => setShowCreateModal(false)}
            onSubmit={handleCreateUser}
            teamId={user.team_id}
          />
        )}

        {showEditModal && selectedUser && (
          <EditUserModal
            user={selectedUser}
            onClose={() => {
              setShowEditModal(false);
              setSelectedUser(null);
            }}
            onSubmit={handleEditUser}
          />
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-md p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error
                </h3>
                <div className="mt-2 text-sm text-red-700">
                  {error}
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

// Componente para crear usuario
const CreateUserModal = ({ onClose, onSubmit, teamId }) => {
  const [formData, setFormData] = useState({
    email: '',
    first_name: '',
    last_name: '',
    role: 'member',
    team_id: teamId
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Crear Nuevo Miembro
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre
              </label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Apellidos
              </label>
              <input
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rol
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="member">Miembro</option>
                <option value="team_lead">Líder de Equipo</option>
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Crear Usuario
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Componente para editar usuario
const EditUserModal = ({ user, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    email: user.email,
    first_name: user.first_name,
    last_name: user.last_name,
    role: user.role
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(user.id, formData);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="mt-3">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            Editar Miembro
          </h3>
          <form onSubmit={handleSubmit}>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Nombre
              </label>
              <input
                type="text"
                required
                value={formData.first_name}
                onChange={(e) => setFormData({...formData, first_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Apellidos
              </label>
              <input
                type="text"
                required
                value={formData.last_name}
                onChange={(e) => setFormData({...formData, last_name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Rol
              </label>
              <select
                value={formData.role}
                onChange={(e) => setFormData({...formData, role: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="member">Miembro</option>
                <option value="team_lead">Líder de Equipo</option>
              </select>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-md"
              >
                Actualizar Usuario
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default TeamManagement;

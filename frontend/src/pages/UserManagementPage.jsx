import React, { useEffect, useState } from 'react';

const UserManagementPage = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    password: '',
    role: 'chef_cuisine',
    full_name: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

  // Available roles with descriptions
  const roles = {
    'super_admin': {
      name: 'Super Admin',
      description: 'Accès complet incluant gestion des utilisateurs',
      icon: '👑',
      color: 'bg-purple-100 text-purple-800'
    },
    'gerant': {
      name: 'Gérant (Manager)',
      description: 'Accès complet sauf gestion utilisateurs - Page Analytics par défaut',
      icon: '👔',
      color: 'bg-blue-100 text-blue-800'
    },
    'chef_cuisine': {
      name: 'Chef de cuisine',
      description: 'Gestion Stock (non-Bar), Production, Commandes, Ajustements stock',
      icon: '👨‍🍳',
      color: 'bg-green-100 text-green-800'
    },
    'barman': {
      name: 'Barman',
      description: 'Gestion Stock catégorie Bar uniquement',
      icon: '🍸',
      color: 'bg-orange-100 text-orange-800'
    },
    'caissier': {
      name: 'Caissier',
      description: 'Accès principal au module OCR pour rapports Z quotidiens',
      icon: '💳',
      color: 'bg-yellow-100 text-yellow-800'
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${backendUrl}/api/admin/users`);
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      } else {
        console.error('Erreur lors du chargement des utilisateurs');
      }
    } catch (error) {
      console.error('Erreur lors du chargement des utilisateurs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitUser = async (e) => {
    e.preventDefault();
    try {
      const method = editingUser ? 'PUT' : 'POST';
      const url = editingUser 
        ? `${backendUrl}/api/admin/users/${editingUser.id}`
        : `${backendUrl}/api/admin/users`;

      const submitData = editingUser 
        ? { ...userForm, password: userForm.password || undefined } // Don't send empty password for updates
        : userForm;

      const response = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(submitData)
      });

      if (response.ok) {
        setShowUserModal(false);
        setEditingUser(null);
        resetUserForm();
        fetchUsers();
        alert(editingUser ? 'Utilisateur modifié avec succès!' : 'Utilisateur créé avec succès!');
      } else {
        const error = await response.json();
        alert(`Erreur: ${error.detail}`);
      }
    } catch (error) {
      console.error('Erreur lors de la sauvegarde:', error);
      alert('Erreur lors de la sauvegarde');
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    setUserForm({
      username: user.username,
      email: user.email,
      password: '', // Don't show password
      role: user.role,
      full_name: user.full_name || ''
    });
    setShowUserModal(true);
  };

  const handleDeleteUser = async (userId, username) => {
    if (window.confirm(`Confirmer la suppression de l'utilisateur "${username}" ?`)) {
      try {
        const response = await fetch(`${backendUrl}/api/admin/users/${userId}`, {
          method: 'DELETE'
        });

        if (response.ok) {
          fetchUsers();
          alert('Utilisateur supprimé avec succès!');
        } else {
          const error = await response.json();
          alert(`Erreur: ${error.detail}`);
        }
      } catch (error) {
        console.error('Erreur lors de la suppression:', error);
        alert('Erreur lors de la suppression');
      }
    }
  };

  const resetUserForm = () => {
    setUserForm({
      username: '',
      email: '',
      password: '',
      role: 'chef_cuisine',
      full_name: ''
    });
  };

  const handleNewUser = () => {
    setEditingUser(null);
    resetUserForm();
    setShowUserModal(true);
  };

  const formatDateTime = (dateStr) => {
    return new Date(dateStr).toLocaleString('fr-FR');
  };

  const getRoleInfo = (roleKey) => {
    return roles[roleKey] || {
      name: roleKey,
      description: 'Rôle inconnu',
      icon: '❓',
      color: 'bg-gray-100 text-gray-800'
    };
  };

  return (
    <div className="p-6 bg-gradient-to-br from-white to-gray-50 min-h-screen">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          👑 Gestion des Utilisateurs
        </h1>
        <p className="text-gray-600">Panneau d'administration pour la gestion des comptes utilisateurs et des rôles</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Utilisateurs</p>
              <p className="text-2xl font-bold text-blue-600">{users.length}</p>
            </div>
            <div className="text-3xl text-blue-500">👥</div>
          </div>
        </div>

        {Object.entries(roles).map(([roleKey, roleInfo]) => {
          const count = users.filter(user => user.role === roleKey).length;
          return (
            <div key={roleKey} className="bg-white p-6 rounded-lg shadow-sm">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{roleInfo.name}</p>
                  <p className="text-2xl font-bold text-gray-800">{count}</p>
                </div>
                <div className="text-3xl">{roleInfo.icon}</div>
              </div>
            </div>
          );
        }).slice(0, 3)} {/* Show only first 3 additional cards */}
      </div>

      {/* Action Button */}
      <div className="mb-6">
        <button
          onClick={handleNewUser}
          className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors flex items-center"
        >
          <span className="mr-2">➕</span>
          Nouvel Utilisateur
        </button>
      </div>

      {/* Users Table */}
      <div className="bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-semibold flex items-center">
              <span className="mr-2">👥</span>
              Utilisateurs du Système
            </h3>
            <button
              onClick={fetchUsers}
              className="text-primary-500 hover:text-primary-600 font-medium flex items-center"
            >
              <span className="mr-1">🔄</span>
              Actualiser
            </button>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto"></div>
              <p className="mt-2 text-gray-600">Chargement des utilisateurs...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Utilisateur</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Email</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Rôle</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Statut</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Créé le</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Dernière connexion</th>
                    <th className="text-left py-3 px-4 font-semibold text-gray-700">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((user) => {
                    const roleInfo = getRoleInfo(user.role);
                    return (
                      <tr key={user.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-3 px-4">
                          <div>
                            <div className="font-medium text-gray-900">{user.username}</div>
                            {user.full_name && (
                              <div className="text-sm text-gray-500">{user.full_name}</div>
                            )}
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">{user.email}</td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${roleInfo.color}`}>
                            <span className="mr-1">{roleInfo.icon}</span>
                            {roleInfo.name}
                          </span>
                        </td>
                        <td className="py-3 px-4">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                          }`}>
                            {user.is_active ? '✅ Actif' : '❌ Inactif'}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {formatDateTime(user.created_at)}
                        </td>
                        <td className="py-3 px-4 text-sm text-gray-600">
                          {user.last_login ? formatDateTime(user.last_login) : 'Jamais connecté'}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex space-x-2">
                            <button
                              onClick={() => handleEditUser(user)}
                              className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                            >
                              ✏️ Modifier
                            </button>
                            {user.role !== 'super_admin' && (
                              <button
                                onClick={() => handleDeleteUser(user.id, user.username)}
                                className="text-red-600 hover:text-red-800 font-medium text-sm"
                              >
                                🗑️ Supprimer
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                  {users.length === 0 && (
                    <tr>
                      <td colSpan="7" className="text-center py-8 text-gray-500">
                        Aucun utilisateur trouvé
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* Roles Information Panel */}
      <div className="mt-8 bg-white rounded-lg shadow-sm">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold flex items-center">
            <span className="mr-2">🔐</span>
            Guide des Rôles et Permissions
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(roles).map(([roleKey, roleInfo]) => (
              <div key={roleKey} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <span className="text-2xl mr-2">{roleInfo.icon}</span>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${roleInfo.color}`}>
                    {roleInfo.name}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{roleInfo.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* User Modal */}
      {showUserModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-md w-full m-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold">
                {editingUser ? 'Modifier l\'utilisateur' : 'Nouvel utilisateur'}
              </h3>
              <p className="text-sm text-gray-600 mt-1">
                {editingUser ? 'Modifiez les informations de l\'utilisateur' : 'Créez un nouveau compte utilisateur'}
              </p>
            </div>
            <form onSubmit={handleSubmitUser} className="p-6">
              <div className="space-y-4">
                {/* Username */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom d'utilisateur *
                  </label>
                  <input
                    type="text"
                    value={userForm.username}
                    onChange={(e) => setUserForm({...userForm, username: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                {/* Email */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email *
                  </label>
                  <input
                    type="email"
                    value={userForm.email}
                    onChange={(e) => setUserForm({...userForm, email: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  />
                </div>

                {/* Password */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Mot de passe {editingUser ? '(laisser vide pour ne pas changer)' : '*'}
                  </label>
                  <input
                    type="password"
                    value={userForm.password}
                    onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required={!editingUser}
                    minLength="6"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Minimum 6 caractères
                  </p>
                </div>

                {/* Full Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Nom complet
                  </label>
                  <input
                    type="text"
                    value={userForm.full_name}
                    onChange={(e) => setUserForm({...userForm, full_name: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                  />
                </div>

                {/* Role */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Rôle *
                  </label>
                  <select
                    value={userForm.role}
                    onChange={(e) => setUserForm({...userForm, role: e.target.value})}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    required
                  >
                    {Object.entries(roles).map(([roleKey, roleInfo]) => (
                      <option key={roleKey} value={roleKey}>
                        {roleInfo.icon} {roleInfo.name} - {roleInfo.description}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Role Description */}
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="text-sm text-gray-600">
                    <strong>Permissions du rôle sélectionné:</strong><br />
                    {getRoleInfo(userForm.role).description}
                  </p>
                </div>
              </div>

              <div className="flex justify-end space-x-3 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowUserModal(false);
                    setEditingUser(null);
                    resetUserForm();
                  }}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="bg-primary-500 hover:bg-primary-600 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  {editingUser ? 'Modifier' : 'Créer'} l'utilisateur
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagementPage;
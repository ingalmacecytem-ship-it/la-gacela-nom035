import React, { useState } from 'react';
import { StyleSheet, Text, TextInput, View, TouchableOpacity, ScrollView, Alert } from 'react-native';

const BACKEND_URL = 'http://10.0.2.2:5000'; // Ajustar al host backend al probar en emulador.

export default function App() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Invitado');
  const [loggedIn, setLoggedIn] = useState(false);
  const [centros, setCentros] = useState([]);
  const [selectedCentro, setSelectedCentro] = useState('');
  const [comentarios, setComentarios] = useState('');

  async function login() {
    try {
      const response = await fetch(`${BACKEND_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });
      const result = await response.json();
      if (result.success) {
        setRole(result.role);
        setLoggedIn(true);
        loadCentros();
      } else {
        Alert.alert('Error', result.message);
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo conectar con el backend.');
    }
  }

  async function loadCentros() {
    try {
      const response = await fetch(`${BACKEND_URL}/api/centros`);
      const data = await response.json();
      setCentros(data);
      if (data.length) {
        setSelectedCentro(String(data[0].id));
      }
    } catch (error) {
      console.warn(error);
    }
  }

  async function registerEvaluation() {
    if (!selectedCentro) {
      Alert.alert('Validación', 'Selecciona un centro primero.');
      return;
    }

    try {
      const response = await fetch(`${BACKEND_URL}/api/evaluacion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          centro_id: Number(selectedCentro),
          tipo_guia: 'II',
          datos: { comentarios },
        }),
      });
      const result = await response.json();
      if (result.success) {
        Alert.alert('Éxito', result.message);
      } else {
        Alert.alert('Error', result.message);
      }
    } catch (error) {
      Alert.alert('Error', 'No se pudo guardar la evaluación.');
    }
  }

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <Text style={styles.title}>La Gacela NOM-035</Text>
      {!loggedIn ? (
        <View style={styles.card}>
          <Text style={styles.label}>Usuario</Text>
          <TextInput style={styles.input} value={username} onChangeText={setUsername} autoCapitalize="none" />
          <Text style={styles.label}>Contraseña</Text>
          <TextInput style={styles.input} secureTextEntry value={password} onChangeText={setPassword} />
          <TouchableOpacity style={styles.button} onPress={login}>
            <Text style={styles.buttonText}>Ingresar</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={styles.card}>
          <Text style={styles.subtitle}>Bienvenido</Text>
          <Text style={styles.role}>Rol: {role}</Text>
          <Text style={styles.label}>Centro de trabajo</Text>
          <View style={styles.picker}>
            {centros.map((centro) => (
              <TouchableOpacity key={centro.id} style={selectedCentro === String(centro.id) ? styles.pickerItemActive : styles.pickerItem} onPress={() => setSelectedCentro(String(centro.id))}>
                <Text>{centro.razon_social}</Text>
              </TouchableOpacity>
            ))}
          </View>
          <Text style={styles.label}>Comentarios</Text>
          <TextInput style={[styles.input, styles.textArea]} value={comentarios} onChangeText={setComentarios} multiline />
          <TouchableOpacity style={styles.button} onPress={registerEvaluation}>
            <Text style={styles.buttonText}>Guardar evaluación</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { backgroundColor: '#eef2ff' },
  content: { padding: 20 },
  title: { fontSize: 28, fontWeight: '700', marginBottom: 20, color: '#1e3a8a' },
  card: { backgroundColor: '#fff', borderRadius: 20, padding: 20, shadowColor: '#000', shadowOpacity: 0.1, shadowRadius: 15, elevation: 4 },
  label: { marginTop: 12, fontWeight: '600', color: '#1f2937' },
  input: { borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 14, padding: 12, marginTop: 8 },
  textArea: { minHeight: 120, textAlignVertical: 'top' },
  button: { backgroundColor: '#4f46e5', padding: 15, borderRadius: 14, marginTop: 18, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: '700' },
  subtitle: { fontSize: 22, fontWeight: '700', marginBottom: 8 },
  role: { marginBottom: 16, color: '#4b5563' },
  picker: { marginTop: 8, gap: 8 },
  pickerItem: { backgroundColor: '#f8fafc', borderRadius: 14, padding: 12 },
  pickerItemActive: { backgroundColor: '#e0e7ff', borderRadius: 14, padding: 12 },
});

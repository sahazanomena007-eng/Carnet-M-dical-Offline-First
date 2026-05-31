"""
Algorithmes pour le carnet medical numerique
- KMP: Recherche rapide dans l'historique
- Greedy: Optimisation des rendez-vous
- DP: Optimisation des prescriptions (sac a dos)
- AVL: Arbre equilibre pour l'historique
- Hash Table: Acces rapide aux patients
- Heap: Gestion des priorites
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import heapq


# ============================================================
# ALGORITHME 1: KMP - Recherche rapide dans l'historique
# Complexite: O(n + m)
# ============================================================

def compute_lps(pattern: str) -> List[int]:
    """Calcule le tableau Longest Prefix Suffix (LPS) pour le pattern"""
    lps = [0] * len(pattern)
    length = 0
    i = 1
    while i < len(pattern):
        if pattern[i] == pattern[length]:
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
    return lps


def kmp_search(text: str, pattern: str) -> List[int]:
    """
    Algorithme KMP pour la recherche de pattern dans un texte.
    Retourne les indices de toutes les occurrences.
    Complexite: O(n + m) ou n = len(text), m = len(pattern)
    """
    if not pattern:
        return [0]

    lps = compute_lps(pattern)
    occurrences = []
    i = j = 0

    while i < len(text):
        if pattern[j] == text[i]:
            i += 1
            j += 1
            if j == len(pattern):
                occurrences.append(i - j)
                j = lps[j - 1]
        else:
            if j != 0:
                j = lps[j - 1]
            else:
                i += 1
    return occurrences


def search_medical_history(consultations: List[Dict], query: str) -> List[Dict]:
    """
    Recherche dans l'historique medical avec KMP.
    Cherche dans les motifs, diagnostics, symptomes et traitements.
    """
    query_lower = query.lower()
    results = []
    for consult in consultations:
        text_fields = [
            consult.get('motif', ''),
            consult.get('symptomes', ''),
            consult.get('diagnostic', ''),
            consult.get('observations', ''),
            consult.get('traitement', ''),
        ]
        full_text = ' '.join(str(f) for f in text_fields if f).lower()
        if kmp_search(full_text, query_lower):
            results.append(consult)
    return results


# ============================================================
# ALGORITHME 2: GREEDY - Optimisation des rendez-vous
# Complexite: O(n log n)
# ============================================================

@dataclass
class Appointment:
    """Represente un rendez-vous pour l'algorithme glouton"""
    id: int
    heure_debut: str
    heure_fin: str
    priorite: int
    motif: str
    patient_nom: str = ""

    def __lt__(self, other):
        """Compare pour le tri: priorite decroissante, puis heure croissante"""
        if self.priorite != other.priorite:
            return self.priorite > other.priorite
        return self.heure_debut < other.heure_debut


def time_to_minutes(t: str) -> int:
    """Convertit HH:MM en minutes"""
    h, m = map(int, t.split(':'))
    return h * 60 + m


def has_overlap(a1: Appointment, a2: Appointment) -> bool:
    """Verifie si deux rendez-vous se chevauchent"""
    s1 = time_to_minutes(a1.heure_debut)
    e1 = time_to_minutes(a1.heure_fin)
    s2 = time_to_minutes(a2.heure_debut)
    e2 = time_to_minutes(a2.heure_fin)
    return s1 < e2 and s2 < e1


def greedy_schedule_optimization(appointments: List[Appointment]) -> Tuple[List[Appointment], List[Tuple[Appointment, Appointment]]]:
    """
    Algorithme glouton pour l'optimisation des rendez-vous.
    1. Trie par priorite decroissante, puis par heure de debut
    2. Selectionne gloutonnement sans conflits
    Complexite: O(n log n) pour le tri + O(n^2) pour la detection de conflits
    """
    # Tri: priorite decroissante, puis heure croissante
    sorted_appts = sorted(appointments)

    # Selection gloutonne
    selected = []
    conflicts = []

    for appt in sorted_appts:
        has_conflict = any(has_overlap(appt, s) for s in selected)
        if not has_conflict:
            selected.append(appt)
        else:
            # Trouver les conflits pour information
            for s in selected:
                if has_overlap(appt, s):
                    conflicts.append((appt, s))

    # Tri final par heure
    selected.sort(key=lambda a: a.heure_debut)
    return selected, conflicts


def find_conflicts(appointments: List[Appointment]) -> List[Dict]:
    """Trouve tous les conflits entre rendez-vous - O(n^2) baseline"""
    conflicts = []
    for i in range(len(appointments)):
        for j in range(i + 1, len(appointments)):
            if has_overlap(appointments[i], appointments[j]):
                s1 = time_to_minutes(appointments[i].heure_debut)
                s2 = time_to_minutes(appointments[j].heure_debut)
                overlap_start = max(s1, s2)
                e1 = time_to_minutes(appointments[i].heure_fin)
                e2 = time_to_minutes(appointments[j].heure_fin)
                overlap_end = min(e1, e2)
                conflicts.append({
                    'rdv1': appointments[i],
                    'rdv2': appointments[j],
                    'overlap': f"{overlap_start // 60:02d}:{overlap_start % 60:02d} - {overlap_end // 60:02d}:{overlap_end % 60:02d}"
                })
    return conflicts


# ============================================================
# ALGORITHME 3: DP - Optimisation des prescriptions (Sac a dos)
# Complexite: O(n x W)
# ============================================================

@dataclass
class Medicament:
    """Represente un medicament pour l'optimisation"""
    nom: str
    cout: float
    efficacite: int
    duree_jours: int


def optimize_prescriptions_dp(medicaments: List[Medicament], budget_max: float) -> Dict:
    """
    Algorithme de programmation dynamique (sac a dos 0/1)
    pour optimiser la selection de medicaments selon le budget.
    Complexite: O(n x W) ou n = nb medicaments, W = budget
    """
    n = len(medicaments)
    W = int(budget_max)

    # dp[i][w] = efficacite maximale avec les i premiers medicaments et budget w
    dp = [[0] * (W + 1) for _ in range(n + 1)]

    # Remplissage du tableau DP
    for i in range(1, n + 1):
        med = medicaments[i - 1]
        cout_int = int(med.cout)
        for w in range(W + 1):
            if cout_int <= w:
                dp[i][w] = max(dp[i - 1][w],
                               dp[i - 1][w - cout_int] + med.efficacite)
            else:
                dp[i][w] = dp[i - 1][w]

    # Backtracking pour retrouver les medicaments selectionnes
    selected = []
    w = W
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            selected.append(medicaments[i - 1])
            w -= int(medicaments[i - 1].cout)

    selected.reverse()
    total_cost = sum(m.cout for m in selected)
    total_efficacy = sum(m.efficacite for m in selected)

    return {
        'selected': selected,
        'total_cost': total_cost,
        'total_efficacy': total_efficacy,
        'budget_used': (total_cost / budget_max) * 100 if budget_max > 0 else 0
    }


# ============================================================
# STRUCTURES DE DONNEES
# ============================================================

# Table de hachage pour les patients
class PatientHashTable:
    """Table de hachage pour l'acces rapide aux patients par numero de dossier"""

    def __init__(self, size: int = 100):
        self.size = size
        self.table = [[] for _ in range(size)]

    def _hash(self, key: str) -> int:
        return hash(key) % self.size

    def insert(self, key: str, patient: Dict):
        idx = self._hash(key)
        for i, (k, _) in enumerate(self.table[idx]):
            if k == key:
                self.table[idx][i] = (key, patient)
                return
        self.table[idx].append((key, patient))

    def get(self, key: str) -> Optional[Dict]:
        idx = self._hash(key)
        for k, v in self.table[idx]:
            if k == key:
                return v
        return None

    def delete(self, key: str):
        idx = self._hash(key)
        self.table[idx] = [(k, v) for k, v in self.table[idx] if k != key]


# Arbre AVL pour l'historique des consultations
@dataclass
class AVLNode:
    """Noeud de l'arbre AVL"""
    key: datetime
    value: Dict
    left: Optional['AVLNode'] = None
    right: Optional['AVLNode'] = None
    height: int = 1


class AVLTree:
    """Arbre AVL pour stocker l'historique des consultations par date"""

    def __init__(self):
        self.root: Optional[AVLNode] = None

    def _height(self, node: Optional[AVLNode]) -> int:
        return node.height if node else 0

    def _balance(self, node: Optional[AVLNode]) -> int:
        return self._height(node.left) - self._height(node.right) if node else 0

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        x = y.left
        T2 = x.right
        x.right = y
        y.left = T2
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        return x

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        y = x.right
        T2 = y.left
        y.left = x
        x.right = T2
        x.height = 1 + max(self._height(x.left), self._height(x.right))
        y.height = 1 + max(self._height(y.left), self._height(y.right))
        return y

    def insert(self, key: datetime, value: Dict):
        self.root = self._insert(self.root, key, value)

    def _insert(self, node: Optional[AVLNode], key: datetime, value: Dict) -> AVLNode:
        if not node:
            return AVLNode(key, value)
        if key < node.key:
            node.left = self._insert(node.left, key, value)
        elif key > node.key:
            node.right = self._insert(node.right, key, value)
        else:
            node.value = value
            return node

        node.height = 1 + max(self._height(node.left), self._height(node.right))
        balance = self._balance(node)

        if balance > 1 and key < node.left.key:
            return self._rotate_right(node)
        if balance < -1 and key > node.right.key:
            return self._rotate_left(node)
        if balance > 1 and key > node.left.key:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)
        if balance < -1 and key < node.right.key:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def inorder(self) -> List[Dict]:
        result = []
        self._inorder(self.root, result)
        return result

    def _inorder(self, node: Optional[AVLNode], result: List[Dict]):
        if node:
            self._inorder(node.left, result)
            result.append(node.value)
            self._inorder(node.right, result)


# Tas (Heap) pour les rendez-vous prioritaires
class AppointmentHeap:
    """Tas min pour gerer les rendez-vous par priorite"""

    def __init__(self):
        self.heap: List[Tuple[int, int, Any]] = []
        self.counter = 0

    def push(self, priority: int, item: Any):
        """Ajoute un element avec une priorite (plus petite = plus prioritaire)"""
        self.counter += 1
        heapq.heappush(self.heap, (priority, self.counter, item))

    def pop(self) -> Any:
        """Retire et retourne l'element avec la plus haute priorite"""
        if self.heap:
            return heapq.heappop(self.heap)[2]
        return None

    def peek(self) -> Any:
        """Retourne l'element avec la plus haute priorite sans le retirer"""
        if self.heap:
            return self.heap[0][2]
        return None

    def __len__(self) -> int:
        return len(self.heap)

    def is_empty(self) -> bool:
        return len(self.heap) == 0

    def to_list(self) -> List[Any]:
        """Retourne tous les elements tries par priorite"""
        return [item for _, _, item in sorted(self.heap)]

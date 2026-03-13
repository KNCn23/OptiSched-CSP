import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Tuple
import pandas as pd
from ortools.sat.python import cp_model

@dataclass
class SchedulerConfig:
    classrooms: List[str] = field(default_factory=lambda: [f'D{i}' for i in range(20)])
    days: List[int] = field(default_factory=lambda: list(range(5)))
    day_map: Dict[int, str] = field(default_factory=lambda: {0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 3: 'Perşembe', 4: 'Cuma'})
    timeslots: List[int] = field(default_factory=lambda: list(range(8)))
    time_map: Dict[int, str] = field(default_factory=lambda: {0: '09:00', 1: '10:00', 2: '11:00', 3: '12:00', 4: '13:00', 5: '14:00', 6: '15:00', 7: '16:00'})
    max_solve_time_seconds: float = 60.0

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataLoader:
    @staticmethod
    def load_data(excel_file: str) -> pd.DataFrame:
        df = pd.read_excel(excel_file)
        expanded = []
        for i, row in df.iterrows():
            t_h = int(row['t_hour']) if pd.notna(row['t_hour']) else 0
            l_h = int(row['l_hour']) if pd.notna(row['l_hour']) else 0
            if t_h > 0:
                expanded.append({
                    'parent_id': i, 
                    'name': f"{row['name']} (T)", 
                    'code': row['code'] if 'code' in row else str(row['name']).split(' ')[0] + ' (T)',
                    'hours': t_h, 
                    'type': 'Teorik', 
                    'dept_id': row['dept_id'], 
                    'program_semester': row['program_semester'], 
                    'instructor': row['instructor']
                })
            if l_h > 0:
                expanded.append({
                    'parent_id': i, 
                    'name': f"{row['name']} (L)", 
                    'code': row['code'] if 'code' in row else str(row['name']).split(' ')[0] + ' (L)',
                    'hours': l_h, 
                    'type': 'Lab', 
                    'dept_id': row['dept_id'], 
                    'program_semester': row['program_semester'], 
                    'instructor': row['instructor']
                })
        return pd.DataFrame(expanded)

class OptiSchedSolver:
    def __init__(self, df: pd.DataFrame, config: SchedulerConfig):
        self.df = df
        self.config = config
        self.model = cp_model.CpModel()
        self.assignments = {}
        self.result_data = []

    def build_model(self) -> None:
        self.start_vars = {}
        # 1. Variables
        for idx, row in self.df.iterrows():
            H = int(row['hours'])
            for d in self.config.days:
                for s in self.config.timeslots:
                    for r in self.config.classrooms:
                        self.assignments[(idx, d, s, r)] = self.model.NewBoolVar(f"c{idx}_d{d}_s{s}_r{r}")
                        if s + H <= len(self.config.timeslots):
                            self.start_vars[(idx, d, s, r)] = self.model.NewBoolVar(f"start_c{idx}_d{d}_s{s}_r{r}")

        # 2. Total hours AND block continuity (Same day, consecutive hours, same room)
        for idx, row in self.df.iterrows():
            H = int(row['hours'])
            valid_starts = []
            
            self.model.Add(sum(self.assignments[(idx, d, s, r)] for d in self.config.days for s in self.config.timeslots for r in self.config.classrooms) == H)

            for d in self.config.days:
                for s in self.config.timeslots:
                    if s + H <= len(self.config.timeslots):
                        for r in self.config.classrooms:
                            s_var = self.start_vars[(idx, d, s, r)]
                            valid_starts.append(s_var)
                            for k in range(H):
                                self.model.AddImplication(s_var, self.assignments[(idx, d, s + k, r)])

            self.model.AddExactlyOne(valid_starts)

        # 3. Lab/Theory Separation: Different Day
        for parent_id in self.df['parent_id'].unique():
            group = self.df[self.df['parent_id'] == parent_id]
            if len(group) == 2:
                t_idx = group[group['type'] == 'Teorik'].index[0]
                l_idx = group[group['type'] == 'Lab'].index[0]
                
                for d in self.config.days:
                    t_day_active = self.model.NewBoolVar(f"t_day_{t_idx}_{d}")
                    self.model.Add(sum(self.assignments[(t_idx, d, s, r)] for s in self.config.timeslots for r in self.config.classrooms) > 0).OnlyEnforceIf(t_day_active)
                    self.model.Add(sum(self.assignments[(t_idx, d, s, r)] for s in self.config.timeslots for r in self.config.classrooms) == 0).OnlyEnforceIf(t_day_active.Not())
                    
                    l_day_active = self.model.NewBoolVar(f"l_day_{l_idx}_{d}")
                    self.model.Add(sum(self.assignments[(l_idx, d, s, r)] for s in self.config.timeslots for r in self.config.classrooms) > 0).OnlyEnforceIf(l_day_active)
                    self.model.Add(sum(self.assignments[(l_idx, d, s, r)] for s in self.config.timeslots for r in self.config.classrooms) == 0).OnlyEnforceIf(l_day_active.Not())
                    
                    self.model.Add(t_day_active + l_day_active <= 1)

        # 4. Global Conflicts (Dept/Semester/Instructor/Room)
        for (dept, sem), group in self.df.groupby(['dept_id', 'program_semester']):
            for d in self.config.days:
                for s in self.config.timeslots:
                    self.model.Add(sum(self.assignments[(idx, d, s, r)] for idx in group.index for r in self.config.classrooms) <= 1)
        
        for instructor in self.df['instructor'].unique():
            if str(instructor) == '-': continue
            inst_group = self.df[self.df['instructor'] == instructor]
            for d in self.config.days:
                for s in self.config.timeslots:
                    self.model.Add(sum(self.assignments[(idx, d, s, r)] for idx in inst_group.index for r in self.config.classrooms) <= 1)

        for r in self.config.classrooms:
            for d in self.config.days:
                for s in self.config.timeslots:
                    self.model.Add(sum(self.assignments[(idx, d, s, r)] for idx in self.df.index) <= 1)

    def solve(self, output_excel: str = 'ders_programi_final_v7.xlsx') -> None:
        solver = cp_model.CpSolver()
        if solver.Solve(self.model) in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            for idx, row in self.df.iterrows():
                for d in self.config.days:
                    for s in self.config.timeslots:
                        for r in self.config.classrooms:
                            if solver.Value(self.assignments[(idx, d, s, r)]):
                                self.result_data.append({
                                    "Gün": self.config.day_map[d], 
                                    "Saat": self.config.time_map[s], 
                                    "Sınıf": r, 
                                    "Ders": row['name'], 
                                    "DersKodu": row['code'],
                                    "Hoca": row['instructor']
                                })
            df_res = pd.DataFrame(self.result_data)
            
            # Create a pivot table for the visual timetable
            pivot_df = df_res.pivot_table(
                index=['Gün', 'Saat'],
                columns='Sınıf',
                values='DersKodu',
                aggfunc=lambda x: '\n'.join(x)
            ).fillna('')
            
            # Enforce sequential order for Days and Times in the Pivot Table
            gün_sirasi = [self.config.day_map[d] for d in self.config.days]
            saat_sirasi = [self.config.time_map[s] for s in self.config.timeslots]
            all_idx = pd.MultiIndex.from_product([gün_sirasi, saat_sirasi], names=['Gün', 'Saat'])
            pivot_df = pivot_df.reindex(all_idx).fillna('')
            
            with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
                df_res.to_excel(writer, sheet_name='Tum_Okul_Liste', index=False)
                pivot_df.to_excel(writer, sheet_name='Gorsel_Program')
                
            print(f"✅ Çizelge hazır: {output_excel}")
        else:
            print("❌ Çözüm bulunamadı!")

if __name__ == '__main__':
    conf = SchedulerConfig()
    loader = DataLoader()
    course_df = loader.load_data('2.xls')
    scheduler = OptiSchedSolver(course_df, conf)
    scheduler.build_model()
    scheduler.solve()

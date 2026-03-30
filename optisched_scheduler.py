"""
OptiSched Scheduler - Academic Course Scheduling Engine

This module implements a Constraint Satisfaction Problem (CSP) solver
using Google OR-Tools to schedule university courses with block requirements
and non-overlapping constraints for students and instructors.
"""

import logging
import sys
import random
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

import pandas as pd
from ortools.sat.python import cp_model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration class for the Scheduler environment."""
    days: List[int] = field(default_factory=lambda: list(range(5)))
    day_map: Dict[int, str] = field(default_factory=lambda: {
        0: 'Pazartesi', 1: 'Salı', 2: 'Çarşamba', 3: 'Perşembe', 4: 'Cuma'
    })
    timeslots: List[int] = field(default_factory=lambda: list(range(8)))
    time_map: Dict[int, str] = field(default_factory=lambda: {
        0: '09:00', 1: '10:00', 2: '11:00', 3: '12:00', 4: '13:00', 
        5: '14:00', 6: '15:00', 7: '16:00'
    })
    max_solve_time_seconds: float = 60.0
    random_seed: int = field(default_factory=lambda: random.randint(1, 100000))


class DataLoader:
    """Handles loading and preprocessing of course data from Excel."""

    @staticmethod
    def load_data(excel_file_path: Path) -> pd.DataFrame:
        """
        Loads and expands course data from an Excel file, splitting multi-hour 
        courses into predefined blocks (e.g., a 5-hour course becomes 3+2).
        
        Args:
            excel_file_path (Path): Path to the input Excel spreadsheet.
            
        Returns:
            pd.DataFrame: Expanded dataframe containing individual schedulable parts.
        """
        logger.info("Loading data from %s...", excel_file_path)
        try:
            df = pd.read_excel(excel_file_path)
        except Exception as e:
            logger.error("Failed to read excel file: %s", e)
            raise

        expanded_data: List[Dict[str, Any]] = []
        for index, row in df.iterrows():
            total_hours = int(row.get('hour', 0)) if pd.notna(row.get('hour')) else 0
            if total_hours <= 0:
                continue
                
            num_sections = int(row.get('seciton', 1)) if 'seciton' in row and pd.notna(row['seciton']) else 1
            if num_sections <= 0:
                num_sections = 1
                
            # Block splitting rules
            if total_hours == 5:
                splits = [3, 2]
            elif total_hours == 4:
                splits = [2, 2]
            elif total_hours == 6:
                splits = [3, 3]
            else:
                splits = [total_hours]
                
            for sec_idx in range(1, num_sections + 1):
                for split_idx, split_hours in enumerate(splits):
                    part_suffix = f" (P{split_idx+1})" if len(splits) > 1 else ""
                    parent_id = f"{index}_{sec_idx}"
                    code_val = f"{str(row.get('code', 'UNK'))}-{sec_idx}"
                    
                    expanded_data.append({
                        'parent_id': parent_id,
                        'name': f"{row.get('name', 'Bilinmeyen Ders')}-{sec_idx}{part_suffix}",
                        'code': code_val,
                        'hours': split_hours,
                        'semester': int(row.get('semester', 0)) if pd.notna(row.get('semester')) else 0,
                        'section': sec_idx,
                        'total_sections': num_sections,
                        'instructor': row.get('lecturer', 'Anonim')
                    })
                
        logger.info("Successfully expanded %d source courses to %d schedulable parts.", len(df), len(expanded_data))
        return pd.DataFrame(expanded_data)


class OptiSchedSolver:
    """Main scheduling engine utilizing Google OR-Tools CP-SAT."""
    
    def __init__(self, course_df: pd.DataFrame, config: SchedulerConfig):
        """
        Initialize the scheduler solver.
        
        Args:
            course_df (pd.DataFrame): The preprocessed course data.
            config (SchedulerConfig): Scheduling configuration and metadata.
        """
        self.df = course_df
        self.config = config
        self.model = cp_model.CpModel()
        self.assignments: Dict[tuple, Any] = {}
        self.start_vars: Dict[tuple, Any] = {}
        self.result_data: List[Dict[str, Any]] = []

    def build_model(self) -> None:
        """Constructs the constraint programming model variables and constraints."""
        logger.info("Building the CP-SAT model variables and constraints...")
        
        # 1. Variables Creation
        for idx, row in self.df.iterrows():
            hours_needed = int(row['hours'])
            for day in self.config.days:
                for slot in self.config.timeslots:
                    # Boolean variable: True if course `idx` is active on `day` at `slot`
                    self.assignments[(idx, day, slot)] = self.model.NewBoolVar(f"c{idx}_d{day}_s{slot}")
                    # Start variable to enforce block continuity
                    if slot + hours_needed <= len(self.config.timeslots):
                        self.start_vars[(idx, day, slot)] = self.model.NewBoolVar(f"start_c{idx}_d{day}_s{slot}")

        # 2. Total hours AND block continuity (Same day, consecutive hours)
        for idx, row in self.df.iterrows():
            hours_needed = int(row['hours'])
            valid_starts = []
            
            # Constraint: Total hours mapped across all timeslots must equal required hours
            self.model.Add(sum(
                self.assignments[(idx, d, s)] 
                for d in self.config.days 
                for s in self.config.timeslots
            ) == hours_needed)

            for d in self.config.days:
                for s in self.config.timeslots:
                    if s + hours_needed <= len(self.config.timeslots):
                        s_var = self.start_vars[(idx, d, s)]
                        valid_starts.append(s_var)
                        
                        # If a course starts at (d, s), it occupies continuous `hours_needed`
                        for k in range(hours_needed):
                            self.model.AddImplication(s_var, self.assignments[(idx, d, s + k)])

            # Constraint: A course part must have exactly one start time across the week
            self.model.AddExactlyOne(valid_starts)

        # 3. Split parts must be on different days
        for parent_id in self.df['parent_id'].unique():
            group = self.df[self.df['parent_id'] == parent_id]
            if len(group) > 1:
                indices = group.index.tolist()
                for d in self.config.days:
                    day_active_vars = []
                    for idx in indices:
                        day_active = self.model.NewBoolVar(f"course_{parent_id}_part_{idx}_day_{d}")
                        # Link `day_active` variable to any scheduled slot on that day
                        self.model.Add(sum(self.assignments[(idx, d, s)] for s in self.config.timeslots) > 0).OnlyEnforceIf(day_active)
                        self.model.Add(sum(self.assignments[(idx, d, s)] for s in self.config.timeslots) == 0).OnlyEnforceIf(day_active.Not())
                        day_active_vars.append(day_active)
                        
                    # Constraint: Parts of the same course cannot occur on the same day
                    self.model.Add(sum(day_active_vars) <= 1)

        # 4. Global Conflicts (Instructor)
        for instructor in self.df['instructor'].unique():
            if pd.isna(instructor) or str(instructor).strip() in ['-', ''] or str(instructor).strip().lower() == 'anonim':
                continue
                
            inst_group = self.df[self.df['instructor'] == instructor]
            for d in self.config.days:
                for s in self.config.timeslots:
                    # Constraint: An instructor teaches at most 1 course per timeslot
                    self.model.Add(sum(self.assignments[(idx, d, s)] for idx in inst_group.index) <= 1)
        
        # 5. Global Conflicts (Semester Logic)
        max_sec = self.df['section'].max() if not self.df.empty else 1
        
        for d in self.config.days:
            for s in self.config.timeslots:
                for sem in range(1, 9):  # Academic semesters (Years 1 to 4 -> Semesters 1 to 8)
                    for sec_id in range(1, max_sec + 1):
                        # Filter courses for current semester and specific section (or common section 1)
                        group_same = self.df[
                            (self.df['semester'] == sem) & 
                            ((self.df['section'] == sec_id) | (self.df['total_sections'] == 1))
                        ].index.tolist()
                        
                        # Filter for same logic but for +2 semesters (i.e. cross-years like Sem 1 and Sem 3)
                        group_next = self.df[
                            (self.df['semester'] == sem + 2) & 
                            ((self.df['section'] == sec_id) | (self.df['total_sections'] == 1))
                        ].index.tolist()
                        
                        # Constraint: Courses in the same semester cohort cannot overlap
                        if group_same:
                            self.model.Add(sum(self.assignments[(idx, d, s)] for idx in group_same) <= 1)
                        
                        # Constraint: Same semester (N) and N+2 (e.g. Sem 1 and Sem 3) cohort cannot overlap
                        if group_same or group_next:
                            self.model.Add(sum(self.assignments[(idx, d, s)] for idx in group_same + group_next) <= 1)

        logger.info("Model built successfully.")

    def solve(self, output_excel_path: Path) -> None:
        """
        Invokes the CP-SAT solver and exports the generated schedule to an Excel file.
        
        Args:
            output_excel_path (Path): Destination path for the resulting Excel file.
        """
        logger.info("Starting CP-SAT solver. Max time limit: %s seconds.", self.config.max_solve_time_seconds)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self.config.max_solve_time_seconds
        solver.parameters.random_seed = self.config.random_seed
        
        # Adding a solver callback could be useful here to log progress
        status = solver.Solve(self.model)
        
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.info("Solver found a viable schedule. Extracting results...")
            for idx, row in self.df.iterrows():
                for d in self.config.days:
                    for s in self.config.timeslots:
                        if solver.Value(self.assignments[(idx, d, s)]):
                            self.result_data.append({
                                "Gün": self.config.day_map[d], 
                                "Saat": self.config.time_map[s], 
                                "Dönem": f"{int(row['semester'])}. Dönem",
                                "Dönem_Int": int(row['semester']),
                                "DersKodu": row['code'],
                                "DersDetay": str(row['code'])
                            })
            
            if not self.result_data:
                logger.warning("Solution is optimal/feasible but no assignments were scheduled.")
                return
                
            self._export_to_excel(output_excel_path)
            
        else:
            logger.error("Solver failed to find a feasible solution under the given constraints.")

    def _export_to_excel(self, output_excel_path: Path) -> None:
        """Internal helper to format and output the data grouping into Excel sheets."""
        try:
            df_res = pd.DataFrame(self.result_data)
            
            output_excel_path.parent.mkdir(parents=True, exist_ok=True)
            
            with pd.ExcelWriter(output_excel_path, engine='openpyxl') as writer:
                # 1. Main flattened list view
                df_list = df_res.drop(columns=['DersDetay', 'Dönem_Int']) if 'Dönem_Int' in df_res.columns else df_res
                df_list.to_excel(writer, sheet_name='Liste_Gorunumu', index=False)
                
                # 2. Individual Sheets Per Day
                for day_id in self.config.days:
                    day_name = self.config.day_map[day_id]
                    day_df = df_res[df_res['Gün'] == day_name]
                    
                    if day_df.empty:
                        pd.DataFrame().to_excel(writer, sheet_name=day_name)
                        continue
                        
                    # Pivot table: Rows = Hours, Columns = Semesters
                    pivot_df = day_df.pivot_table(
                        index='Saat',
                        columns='Dönem',
                        values='DersDetay',
                        aggfunc=lambda x: '\n\n'.join(x)
                    ).fillna('')
                    
                    time_idx_order = [self.config.time_map[s] for s in self.config.timeslots]
                    valid_rows = [r for r in time_idx_order if r in pivot_df.index]
                    unique_sems = sorted(day_df['Dönem_Int'].unique())
                    col_order = [f"{s}. Dönem" for s in unique_sems]
                    
                    pivot_df = pivot_df.reindex(index=valid_rows, columns=col_order).fillna('')
                    pivot_df.to_excel(writer, sheet_name=day_name)
                    
            logger.info("✅ Schedule successfully exported to '%s'.", output_excel_path)
        except Exception as e:
            logger.error("Failed to write to excel file: %s", e)
            raise


def parse_arguments() -> argparse.Namespace:
    """Parses command-line arguments for the application."""
    parser = argparse.ArgumentParser(
        description="OptiSched: Smart Academic Block Scheduler using CSP"
    )
    
    parser.add_argument(
        '--term', 
        type=str, 
        required=True,
        choices=['guz', 'bahar', 'fall', 'spring'],
        help="Target semester group to schedule (guz/fall for odd semesters, bahar/spring for even semesters)."
    )
    
    parser.add_argument(
        '--input', 
        type=Path, 
        default=Path('data/bil 2.xlsx'),
        help="Path to the source Excel file containing course information."
    )
    
    parser.add_argument(
        '--output', 
        type=Path, 
        default=Path('output/'),
        help="Path to the output directory where the final Excel file will be saved."
    )
    
    return parser.parse_args()


def main() -> None:
    """Main execution function for the scheduler engine."""
    args = parse_arguments()
    
    term_input = args.term.lower()
    is_fall = term_input in ['guz', 'fall']
    term_name = "Guz" if is_fall else "Bahar"
    
    input_path = args.input
    if not input_path.exists():
        logger.error("Input file not found at: %s. Reverting to default or aborting.", input_path)
        sys.exit(1)
        
    output_dir = args.output
    output_file = output_dir / f"ders_programi_{term_name}.xlsx"

    # Initialization
    config = SchedulerConfig()
    loader = DataLoader()
    
    try:
        course_df = loader.load_data(input_path)
    except Exception:
        sys.exit(1)
    
    if course_df.empty:
        logger.error("Failed or found no valid data from %s", input_path)
        sys.exit(1)

    # Filter semesters logic: Fall (Odd 1, 3, 5, 7), Spring (Even 2, 4, 6, 8)
    initial_course_count = len(course_df)
    if is_fall:
        course_df = course_df[course_df['semester'] % 2 != 0].reset_index(drop=True)
    else:
        course_df = course_df[course_df['semester'] % 2 == 0].reset_index(drop=True)
        
    filtered_course_count = len(course_df)
    logger.info("Filtered for %s term: Reduced %d parts -> %d active schedule parts.", 
                term_name.upper(), initial_course_count, filtered_course_count)
    
    if course_df.empty:
        logger.warning("No courses matched the criteria for term '%s'. Exiting.", term_name)
        sys.exit(0)

    # Initialize and Solve
    scheduler = OptiSchedSolver(course_df, config)
    scheduler.build_model()
    
    logger.info("Solving... Result will be written to '%s'.", output_file)
    scheduler.solve(output_excel_path=output_file)


if __name__ == '__main__':
    main()

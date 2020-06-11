import textx
import textx.export

grammar = """
	FileName:
		Configuration | /[^\/]*\// FileName
	;
	
	Configuration:
		(
			config = VacuumConfiguration
			('beta' beta_ax = RestrictedNumber)?
			(('Lc' | 'LC' | 'lc') lc = RestrictedNumber ('m' | 'M')?)?
			('itor' '+'? itor = RestrictedNumber)?
			(pressure_profile = PressureProfile)?
			(current_profile  = CurrentProfile)?
			('D' diffusion_coefficient = RestrictedNumber)?
			vacuum_tag ?= 'vacuum'
		)#[/[-\/]/]
		vacfile_tag ?= /[\.\/]vacfile/
		(/[\.\/]snapfile\./ snap_id = INT)?
		('.' extension = /[0-9a-zA-Z\\.]+/)?
	;
	
	VacuumConfiguration:
		'op' op = RestrictedNumber
		'-'
		(name = ID)
		('-' 'cw' cw = RestrictedNumber 'cm')?
	;
	
	PressureProfile:
		ParabolicPressureProfile | DischargePressureProfile
	;
	
	ParabolicPressureProfile:
		'parabolic' '_'? baseline = RestrictedNumber '_' inner_exponent = RestrictedNumber '_' outer_exponent = RestrictedNumber
	;
	
	DischargePressureProfile:
		'profile' program = Shot
	;
	
	Shot: ProgramNo | MDSPlusShot;
	
	ProgramNo:
		year  = /[0-9]{4}/
		month = /[0-9]{2}/
		day   = /[0-9]{2}/
		'.' no = INT
	;
	
	MDSPlusShot:
		str = /[1-9][0-9]{8}/
	;
	
	CurrentProfile:
		ExponentialCurrentProfile
	;
	
	ExponentialCurrentProfile:
		'pow' exponent = RestrictedNumber
	;
	
	RestrictedNumber:
		/[+-]?[0-9]*([.][0-9]+)?(e[0-9]*)?/
	;
"""

class ParabolicPressureProfile:
	def __init__(self, parent, baseline = 0.02, inner_exponent = 1, outer_exponent = 1):
		self.parent = parent
		self.baseline = baseline
		self.outer_exponent = outer_exponent
		self.inner_exponent = inner_exponent

class ExponentialCurrentProfile:
	def __init__(self, parent, exponent = 1):
		self.parent = parent
		self.exponent = exponent

class DischargePressureProfile:
	def __init__(self, parent, program):
		self.parent = parent
		self.program   = program

class VacuumConfiguration:
	def __init__(self, parent, op = '12', name = 'standard', cw = 0):
		self.parent = parent
		self.op     = op
		self.name   = name
		self.cw     = 0 if cw is None else cw

class ProgramNo:
	def __init__(self, parent, year, month, day, no):
		self.parent = parent
		self.year = int(year)
		self.month = int(month)
		self.day = int(day)
		self.no = int(no)
	
	def __repr__(self):
		return '{:04d}{:02d}{:02d}.{}'.format(self.year, self.month, self.day, self.no)
	
	def as_mdsplus(self):
		yearlast = str(year)[2:4]
		return '{}{:02d}{:02d}{:03d}'.format(yearlast, self.month, self.day, self.no)
	
	def as_three_digit_program(self):
		return '{:04d}{:02d}{:02d}.{:03d}'.format(self.year, self.month, self.day, self.no)

class Configuration:
	def __init__(
		self, config, beta_ax = None, lc = None, itor = None,
		pressure_profile = None, current_profile = None, vacuum_tag = False, vacfile_tag = False, snap_id = None, extension = None,
		diffusion_coefficient = None
	):
		self.config = config
		self.beta_ax = 0 if beta_ax is None else beta_ax
		self.lc = 20 if lc is None else lc
		self.itor = 0 if itor is None else itor
		self.pressure_profile = ParabolicPressureProfile(self) if pressure_profile is None else pressure_profile
		self.current_profile = ExponentialCurrentProfile(self) if current_profile is None else current_profile
		self.vacuum_tag = vacuum_tag
		self.vacfile_tag = vacfile_tag
		self.snap_id = snap_id
		self.extension = extension
		self.diffusion_coefficient = diffusion_coefficient
	
	def strip_extra_info(self):
		return Configuration(
			config = self.config,
			beta_ax = self.beta_ax,
			lc = self.lc,
			itor = self.itor,
			pressure_profile = self.pressure_profile,
			current_profile = self.current_profile,
			diffusion_coefficient = self.diffusion_coefficient
		)
	
	def __str__(x):
		# Number conversion that puts out integer floats without dot
		def num2str(x):
			if isinstance(x, float) and x.is_integer():
				x = int(x)
			
			return str(x)
			
		c = x.config
		s = 'op{}-{}'.format(num2str(c.op), c.name)
		
		if c.cw != 0:
			s += '-cw' + num2str(c.cw) + 'cm'
		
		if x.beta_ax != 0:
			s += '-beta' + num2str(x.beta_ax)
		
		pp = x.pressure_profile
		if isinstance(pp, DischargePressureProfile):
			s += '-profile' + str(pp.program)
		elif isinstance(pp, ParabolicPressureProfile):
			if pp.baseline != 0.02 or pp.outer_exponent != 1 or pp.inner_exponent != 1:
				s += '-parabolic_{}_{}_{}'.format(
					num2str(pp.baseline),
					num2str(pp.inner_exponent),
					num2str(pp.outer_exponent)
				)
		
		if x.itor != 0:
			sign = '+' if x.itor > 0 else ''
			s += '-itor' + sign + num2str(x.itor)
		
		exp = x.current_profile.exponent
		if exp != 1:
			s += '-pow' + num2str(exp)
		
		if x.lc != 20:
			s += '-lc' + num2str(x.lc) + 'm'
		
		if x.vacuum_tag:
			s += '-vacuum'
		
		if x.vacfile_tag:
			s += '.vacfile'
		
		if x.snap_id != None:
			s += '.snapfile.' + str(x.snap_id)
		
		if x.extension:
			s += '.' + x.extension
		
		return s
		
classes = [
	ParabolicPressureProfile,
	ExponentialCurrentProfile,
	DischargePressureProfile,
	VacuumConfiguration,
	Configuration,
	ProgramNo
]

# Conversion from MDSplus no. to program number

def convert_mdsplus_shot(x):
	year = '20' + x.str[:2]
	month = x.str[2:4]
	day = x.str[4:6]
	no = x.str[6:]
	
	return ProgramNo(x.parent, year, month, day, no)

def convert_restricted_float(x):
	try:
		return int(x)
	except:
		pass
	
	return float(x)
	

mm = textx.metamodel_from_str(grammar, auto_init_attributes = False, classes = classes)
mm.register_obj_processors({
	'RestrictedNumber': float,
	'MDSPlusShot' : convert_mdsplus_shot
})

def from_str(x):
	return mm.model_from_str(x)
	
if __name__ == '__main__':
	def test(x):
		m = from_str(x)
		print(m)
		m2 = m.strip_extra_info()
		print(m2)
		
	test('.././op12-standard-cw1cm/beta0.05-pow2.0-profile20170809.0000002-itor-4.0/lc2m.snapfile.80.nc.test.mat')
	test('op12-high_iota-cw1cm/itor-5-D4-vacuum.nc')
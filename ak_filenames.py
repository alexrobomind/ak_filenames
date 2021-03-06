import textx
import textx.export

grammar = """
	FileName:
		Configuration | /[^\\/\\\\]*[\\/\\\\]/ FileName
	;
	
	Configuration:
		(
			config = VacuumConfiguration
			('beta' beta_ax = RestrictedNumber)?
			(('Lc' | 'LC' | 'lc') lc = RestrictedNumber ('m' | 'M')?)?
			('itor' '+'? itor = RestrictedNumber)?
			(pressure_profile = PressureProfile)?
			(current_profile  = CurrentProfile)?
			('nr' nr = INT)?
			('nz' nz = INT)?
			('nphi' nphi = INT)?
			('nsym' nsym = INT)?
			('D' diffusion_coefficient = RestrictedNumber)?
			('view-' view = ID)?
			('vacuum')?
		)#[/[-\\/\\\\]/]
		(/[\\.\\/\\\\]vacfile/)?
		(/[\\.\\/\\\\]snapfile\./ snap_id = INT)?
		('.' extension = /[0-9a-zA-Z\\.]+/)?
	;
	
	VacuumConfiguration:
		'op' op = RestrictedNumber
		'-'
		(name = ID)
		('-' 'cw' cw = RestrictedNumber 'cm')?
	;
	
	PressureProfile:
		ParabolicPressureProfile | DischargePressureProfile | ('poly' ('_')? PolynomialProfile)
	;
	
	ParabolicPressureProfile:
		('parabolic' | 'am0') '_'? baseline = RestrictedNumber '_' inner_exponent = RestrictedNumber '_' outer_exponent = RestrictedNumber
	;
	
	DischargePressureProfile:
		'profile' program = Shot
	;
	
	PolynomialProfile:
		coefficients += RestrictedNumber['_']
	;
	
	Shot: ProgramNo | MDSPlusShot;
	
	ProgramNo:
		year  = /[0-9]{4}/
		month = /[0-9]{2}/
		day	  = /[0-9]{2}/
		'.' no = INT
	;
	
	MDSPlusShot:
		str = /[1-9][0-9]{8}/
	;
	
	CurrentProfile:
		ExponentialCurrentProfile | ('jpoly' ('_')? PolynomialProfile)
	;
	
	ExponentialCurrentProfile:
		'pow' exponent = RestrictedNumber
	;
	
	RestrictedNumber:
		/[+-]?[0-9]*([.][0-9]+)?(e[0-9]*)?/
	;
"""

class DataClass:
	def __eq__(self, other):
		if type(self) is not type(other):
			return False
		
		if self.fields() != other.fields():
			return False
		
		return True
	
	def __hash__(self):
		hashval = 0
		
		for f in self.fields():
			hashval ^= hash(f)
		
		return hashval

class ParabolicPressureProfile(DataClass):
	def __init__(self, parent, baseline = 0.02, inner_exponent = 1, outer_exponent = 1):
		self.parent = parent
		self.baseline = baseline
		self.outer_exponent = outer_exponent
		self.inner_exponent = inner_exponent
	
	def fields(self):
		return [self.baseline, self.outer_exponent, self.inner_exponent]

class ExponentialCurrentProfile(DataClass):
	def __init__(self, parent, exponent = 1):
		self.parent = parent
		self.exponent = exponent
	
	def fields(self):
		return [self.exponent]

class DischargePressureProfile(DataClass):
	def __init__(self, parent, program):
		self.parent = parent
		self.program = program
	
	def fields(self):
		return [self.program]

class PolynomialProfile(DataClass):
	def __init__(self, parent, coefficients = []):
		self.parent = parent
		self.coefficients = tuple(coefficients)
	
	def fields(self):
		return [self.coefficients]

class VacuumConfiguration(DataClass):
	def __init__(self, parent, op = '12', name = 'standard', cw = 0):
		self.parent = parent
		self.op		= op
		self.name	= name
		self.cw		= 0 if cw is None else cw
	
	def fields(self):
		return [self.op, self.name, self.cw]

class ProgramNo(DataClass):
	def __init__(self, parent, year, month, day, no):
		self.parent = parent
		self.year = int(year)
		self.month = int(month)
		self.day = int(day)
		self.no = int(no)
	
	def fields(self):
		return [self.year, self.month, self.day, self.no]
	
	def __repr__(self):
		return '{:04d}{:02d}{:02d}.{}'.format(self.year, self.month, self.day, self.no)
	
	def as_mdsplus(self):
		yearlast = str(year)[2:4]
		return '{}{:02d}{:02d}{:03d}'.format(yearlast, self.month, self.day, self.no)
	
	def as_three_digit_program(self):
		return '{:04d}{:02d}{:02d}.{:03d}'.format(self.year, self.month, self.day, self.no)

class Configuration(DataClass):
	def __init__(
		self, config, beta_ax = None, lc = None, itor = None,
		pressure_profile = None, current_profile = None, vacuum_tag = False, vacfile_tag = False, snap_id = None, extension = None,
		diffusion_coefficient = None, view = None,
		nr = None, nz = None, nphi = None, nsym = None
	):
		self.config = config
		self.beta_ax = 0 if beta_ax is None else beta_ax
		self.lc = 10 if lc is None else lc
		self.itor = 0 if itor is None else itor
		self.pressure_profile = ParabolicPressureProfile(self) if pressure_profile is None else pressure_profile
		self.current_profile = ExponentialCurrentProfile(self) if current_profile is None else current_profile
		self.snap_id = snap_id
		self.extension = extension
		self.diffusion_coefficient = diffusion_coefficient
		self.view = view
		self.nr = 256 if nr is None else nr
		self.nz = 256 if nz is None else nz
		self.nphi = 128 if nphi is None else nphi
		self.nsym = 5 if nsym is None else nsym
	
	def strip_extra_info(self):
		return Configuration(
			config = self.config,
			beta_ax = self.beta_ax,
			lc = self.lc,
			itor = self.itor,
			pressure_profile = self.pressure_profile,
			current_profile = self.current_profile,
			diffusion_coefficient = self.diffusion_coefficient,
			view = self.view
		)
	
	def fields(self):
		return [
			self.config,
			self.beta_ax,
			self.lc,
			self.itor,
			self.pressure_profile,
			self.current_profile,
			self.snap_id,
			self.extension,
			self.diffusion_coefficient,
			self.view
		]
	
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
		else:
			s += '-vacuum'
		
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
		elif isinstance(pp, PolynomialProfile):
			s += '-poly'
			
			for c in pp.coefficients:
				s += '_' + str(c)
		
		if x.itor != 0:
			sign = '+' if x.itor > 0 else ''
			s += '-itor' + sign + num2str(x.itor)
		
		cp = x.current_profile
		
		if isinstance(cp, ExponentialCurrentProfile):
			exp = x.current_profile.exponent
			if exp != 1:
				s += '-pow' + num2str(exp)
		elif isinstance(cp, PolynomialProfile):
			s += '-jpoly'
			
			for c in cp.coefficients:
				s += '_' + str(c)
		
		if x.lc != 10:
			s += '-lc' + num2str(x.lc) + 'm'
		
		if x.nr != 256:
			s += '-nr' + str(x.nr)
		
		if x.nz != 256:
			s += '-nz' + str(x.nz)
		
		if x.nphi != 128:
			s += '-nphi' + str(x.nphi)
		
		if x.nsym != 5:
			s += '-nsym' + str(x.nsym)
			
		if x.diffusion_coefficient is not None:
			s += '-D' + num2str(x.diffusion_coefficient)
		
		if x.view:
			s += '-view-' + x.view
		
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
	ProgramNo,
	PolynomialProfile
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
		print(m.current_profile)
		print(m.pressure_profile)
		print(hash(m))
		m2 = m.strip_extra_info()
		print(m2)
		print(m == m2)
		
	test('../.\\op12-standard-cw1cm/beta0.05-pow2.0-profile20170809.0000002-itor-4.0/lc2m.snapfile.80.nc.test.mat')
	test('op12-high_iota-cw1cm/itor-5-D4-view-divertor.nc')
	test('op12-high_iota-cw1cm/itor-5-D4-view-divertor-poly0_-1-jpoly_-1_0.nc')
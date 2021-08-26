#!/usr/bin/perl

=pod
=head1 City URLs

The purpose of this perl snippet is to generate the URLs inside the iframe
to embed covSPECTRUM per-city summaries into the projet page.

=encoding utf8
=cut

use strict;

my %locs = (
	'SG' => 'Altenrhein%20%28SG%29',
	'GR' => 'Chur%20%28GR%29',
	'GE' => 'Gen%C3%A8ve+%28GE%29',
	'BE' => 'Laupen%20%28BE%29',
	'VD' => 'Lausanne%20%28VD%29',
	'TI' => 'Lugano%20%28TI%29',
	'ZH' => 'Z%C3%BCrich%20%28ZH%29',
);

for my $k ('SG','GR','BE','VD','TI','ZH') {
	my $loc = $locs{$k};

	my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime();
	my $d = sprintf '%02u-%02u', ++$mon, $mday;

	my $url = "https://cov-spectrum.ethz.ch/embed/WasteWaterLocationTimeChart?json=%7B%22country%22%3A%22Switzerland%22%2C%22location%22%3A%22$loc%22%7D&sharedWidgetJson=%7B%22originalPageUrl%22%3A%22https%3A%2F%2Fcov-spectrum.ethz.ch%2Fstory%2Fwastewater-in-switzerland%22%7D";
	print <<IFR
<br>
<!-- $k $d -->
<div style="position: relative; width:100%;min-height:300px; padding-top:
56.25%"><iframe src="$url" style="position:absolute;top:0;left:0;bottom:0;right:0;" width="100%" height="100%" frameborder="0"></iframe></div>
<br>

IFR
}

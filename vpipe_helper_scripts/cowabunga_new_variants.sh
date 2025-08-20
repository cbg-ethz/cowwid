#!/bin/bash

umask 0007

scriptdir="$(dirname $(which $0))"
baseconda="$scriptdir/"

working=working
worktest=work-new-variants
sampleset=sampleset

#
# Input validator
#
validateBatchName() {
	if [[ "$1" =~ ^(20[0-9][0-9][0-1][0-9][0-3][0-9]_[[:alnum:]-]{4,})$ ]]; then
		return;
	else
		echo "bad batchname ${1}"
		exit 1;
	fi
}

validateProto() {
	case "$1" in
		v3|v4|v41|v532)
			return
		;;
		*)
			echo "bad proto ${1}"
			exit 1;
		;;
	esac
}



lastmonth=$(date '+%Y%m' --date='-1 month')
thismonth=$(date '+%Y%m')
thisyear=$(date '+%Y')

case "$1" in
	autoaddww|autoaddwastewater)
                if [[ -z "$2" ]] || [[ "$2" != "last_month" &&  "$2" != "this_month" && "$2" != "year" && "$2" != "all" ]]; then
                        echo "Usage: $0 $1 <TIMEFRAME>" 1>&2;
			echo "Accepted timeframes: last_month, this_month, year, all"
                        exit 0
                fi
		
		timeframe=$2
		if [[ "$timeframe" == "last_month" ]]; then
			custom_date=$lastmonth
		elif [[ "$timeframe" == "this_month" ]]; then
                        custom_date=$thismonth
		elif [[ "$timeframe" == "year" ]]; then
			custom_date=$thisyear
		elif [[ "$timeframe" == "all" ]]; then
                        custom_date="2"
		fi

		projects=( 'p23224' 'p24991' 'p26177' 'p30045' )
		projpat="$( ( IFS='|';echo "${projects[*]}" ) )"
		gawk -v d="${custom_date}" '$2<d' ${working}/samples.wastewateronly.tsv > ${working}/samples.wastewateronly.tsv.old
		{
			# assemble samples.wastewateronly.tsv
			{
				printf '%s\n' ${sampleset}/projects.${custom_date}*.tsv | grep -vF '*' | sort -r | while read p; do
					echo -n "${p} - ${p//projects/samples} ... " >&2
					gawk -v projpat="${projpat}" '(FILENAME~/\/projects\./)&&($2~projpat){ww[$1]++;nww++};(FILENAME~/\/samples\./)&&(ww[$1]);END{print nww >> "/dev/stderr"}' "${p}" "${p//projects/samples}"
				done | tee >(cut -f4 >&3) # pass the protos to the second part bellow
				cat ${working}/samples.wastewateronly.tsv.old
			} > ${working}/samples.wastewateronly.tsv
		} 3>&1 | sort | uniq -c | while read cnt PROTO o; do
			echo "proto: ${PROTO} (${cnt})"
			gawk -v proto="${PROTO}" '$4==proto' ${working}/samples.wastewateronly.tsv > ${working}/samples.wastewateronly.${PROTO}.tsv
		done;
	;;

	shufflebatches)
		if [[ -z "$2" || "$2" == "--help" ]]; then
			echo "Usage: $0 $1 <BATCH>" 1>&2;
			exit 0
		fi

		BATCH=$2
		validateBatchName "${BATCH}"

		# check existing
		if [[ ! -e "sampleset/samples.${BATCH}.tsv" ]]; then
			echo "Cannot find batch ${BATCH}" >&2
			exit 1
		fi

		echo "batch ${BATCH}"

		# majority votre proto
		read cnt PROTO o < <(cut -f4 sampleset/samples.${BATCH}.tsv | sort | uniq -c | tee /dev/stderr)
		echo "proto: ${PROTO}"

		#
		# Proto validate + specific files
		#
		case "${PROTO}" in
			v3)	bedfile="cojac/nCoV-2019.insert.${PROTO^^}.bed"	;;
			v4)	bedfile="cojac/SARS-CoV-2.insert.${PROTO^^}.txt"	;;
			v41)	bedfile="cojac/SARS-CoV-2.insert.${PROTO^^}.bed"	;;
			*)
				echo "bad proto ${PROTO}"
				exit 1;
			;;
		esac
		allprototsv=( ${working}/samples.wastewateronly.{v41,v4,v3}.tsv )
		if [[ ! -r "${bedfile}" ]]; then
			echo "missing bedfile ${bedfile}"
			exit 1;
		fi

		# 'lastweek' backup
		if grep -qF "${BATCH}" ${working}/samples.wastewateronly${PROTO:+.${PROTO}}.tsv; then
			echo "using:"
			ls -l ${working}/samples.wastewateronly${PROTO:+.${PROTO}}{,.lastweek,.thisweek}.tsv
		else
			echo "backing up lastweek:"
			cp -v ${working}/samples.wastewateronly${PROTO:+.${PROTO}}{,.lastweek}.tsv
		fi

		(grep -vP '^(Y\d{2,}|NC|\d{6,})' "sampleset/samples.${BATCH}.tsv" | tee ${working}/samples.wastewateronly${PROTO:+.${PROTO}}.thisweek.tsv ; cat ${working}/samples.wastewateronly${PROTO:+.${PROTO}}.lastweek.tsv) > ${working}/samples.wastewateronly${PROTO:+.${PROTO}}.tsv
		cat "${allprototsv[@]}" > ${working}/samples.wastewateronly.tsv
	;;

	bring_results)
		TSV=samples.wastewateronly.tsv
		overwrite=0
		if [[ -n "$2" ]]; then
			case "$2" in
				--overwrite)
					overwrite=1
				;;
				*)
					echo "Unkown parameter ${2}" > /dev/stderr
					exit 2
				;;
			esac
		fi

		# bring current list in
		if cp ${scriptdir}/${working}/${TSV} ${scriptdir}/${worktest}/; then
			ln -sf "${TSV}" ${worktest}/samples.tsv
		else
			echo "Cannot find ${TSV}"
			exit 1
		fi

		if (( overwrite )); then
			echo "Entirely rebuilding results/ directory"
		else
			echo "Appending missing samples to results/ directory"
		fi

		mkdir -p ${worktest}/results/

		while read s b o; do
			rmdir --ignore-fail-on-non-empty ${worktest}/results/${s}/${b}/
			if (( overwrite )); then
				rm -rvf ${worktest}/results/${s}/${b}/
			elif [[ -e ${worktest}/results/${s}/${b}/ ]]; then
				continue
			fi

			mkdir -p ${worktest}/results/${s}/${b}/
			if grep -q ${s} lollipop_blacklist.txt || grep -q ${b} lollipop_blacklist.txt; then
				echo "Skipping ${worktest}/results/${s}/${b}/ in lollipop_blacklist.txt"
			else
				cp -alv ${working}/samples/${s}/${b}/{references,alignments} ${worktest}/results/${s}/${b}/
			fi
		done < ${worktest}/${TSV}
		for i in $(cat lollipop_blacklist.txt); do
			while read -r line
			do
				[[ ! $line =~ $i ]] && echo "$line"
			done <${worktest}/${TSV} > ${worktest}/${TSV}_temp
			mv ${worktest}/${TSV}_temp ${worktest}/${TSV}
		done
	;;

	fetch_cooc)
		proto=${2:-v532}
		validateProto "${proto}"
		echo "fetching ${proto}:"

		gawk -v proto="${proto}" '$4==proto' ${worktest}/samples.tsv | while read s b o; do cat ${worktest}/results/${s}/${b}/signatures/cooc.yaml; echo -n '.' >&2; done > ${worktest}/cooc.${proto}.yaml
		echo "done"
	;;

	export)
		base_ww=/cluster/project/pangolin/work-new-variants
		base_main=/cluster/project/pangolin/working
		export_base=/cluster/project/pangolin/export

		timeline="${base_ww}/variants/timeline.tsv" # TODO marge with main in the future
		mainresults="${base_main}/samples/" # TODO switch to results in the future
		tail -n +2 "${timeline}" | while read s b o; do
			#mkdir -p --mode=0775 ${export_base}/{,${s}/{,${b}/{,uploads/,alignments/}}}
			install  --preserve-timestamps --mode=0775  -D --directory "${export_base}/${s}/${b}/"{uploads,alignments}/
			install  --preserve-timestamps --mode=0664  -D --target-directory="${export_base}/${s}/${b}/alignments/" "${mainresults}/${s}/${b}/alignments/"{dehuman.count,REF_aln_stats.yaml}
			cp --link -vf "${mainresults}/${s}/${b}/uploads/dehuman.cram"* "${export_base}/${s}/${b}/uploads/"
			chmod o+r "${export_base}/${s}/${b}/uploads/dehuman.cram"*
		done
	;;

	*)
		echo "Unkown subcommand ${1}" > /dev/stderr
		exit 2
	;;
esac

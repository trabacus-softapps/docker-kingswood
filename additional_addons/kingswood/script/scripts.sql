-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- 				FUNCTION:Purchase summary for Done records
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
drop type if exists po_data cascade;

create type po_data as (id int,   
	  name varchar(50), 
	  date date,
	  default_code varchar(50),
	  truck_no varchar(100),
	  product_qty numeric,
	  unloaded_qty numeric,
	  price_unit numeric,
	  amount numeric,
	  freight_paid numeric,
	  amount_payable numeric,
	  rejected_qty numeric,
	  deduction_amt numeric,
	  ded_amount numeric, 
	  opening_balance numeric,
	  closing_balance numeric,
	  company varchar(100)
	  ); 

 drop function if exists purchase_smry(start_dt date, sup integer, inv_id integer);
 



CREATE OR REPLACE FUNCTION purchase_smry(start_dt date, sup integer, inv_id integer)
  RETURNS SETOF po_data AS
$BODY$
    DECLARE
       r po_data%rowtype;
       st_date timestamp;
       open_bal numeric(16,2) :=0; 
       curr_closebal numeric(16,2) :=0;
       prev_closebal numeric(16,2) :=0;
       delivery_count integer;
       amount_count integer;
       rec record;
       i integer :=1;
       
    BEGIN
    	st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh24:mi:ss');
    
    
    	DROP SEQUENCE if exists do_seq;
    	CREATE TEMP sequence do_seq;
    
    	DROP SEQUENCE if exists pay_seq;
    	CREATE TEMP sequence pay_seq;
    	
        DROP TABLE if exists tmp_del_orders;
        CREATE TEMP TABLE tmp_del_orders
    	( id int,   
    	  name varchar(50), 
    	  date date,
    	  default_code varchar(50),
    	  truck_no varchar(100),
    	  product_qty numeric,
    	  unloaded_qty numeric,
    	  price_unit numeric,
    	  amount numeric,
    	  freight_paid numeric,
    	  amount_payable numeric,
    	  rejected_qty numeric,
    	  deduction_amt numeric,
    	  ded_amount numeric,
    	  opening_balance numeric,
    	  closing_balance numeric,
    	  company varchar(100) 
    	  
    	)
         ON COMMIT DROP;
    
    	 DROP TABLE if exists tmp_amount;
    	create temp table tmp_amount
    	(
    	    id int,   
    	   amount numeric	
    	)
    	ON COMMIT DROP;
         
         INSERT INTO tmp_del_orders(id, name, date, default_code, truck_no,product_qty,unloaded_qty, price_unit,amount,freight_paid,amount_payable,rejected_qty
         ,deduction_amt,ded_amount,company )
         ( SELECT nextval('do_seq') as id 
    	 , data.name
             , data.date
             , data.default_code
             , data.truck_no  
             , data.product_qty
             , data.unloaded_qty
             , data.price_unit
             , (data.unloaded_qty * data.price_unit) as amount  
             , data.freight_paid
             , (data.unloaded_qty * data.price_unit - data.freight_balance ) as amount_payable
             , data.rejected_qty  
             , data.deduction_amt
             , (data.rejected_qty * data.price_unit + data.deduction_amt) as ded_amount
             , data.ref
              FROM
    		(  (select
    			sp.name
    			,sp.date
    			,p.default_code
    			,sp.truck_no
    			,sm.product_qty
    			,sm.unloaded_qty
			, case when i.freight=false then(select k.product_price from kw_product_price k 
			inner join product_supplierinfo ps on ps.id = k.supp_info_id
			where ps.product_id = sm.product_id and ps.name = sup  and k.ef_date < st_date::date order by k.ef_date desc limit 1) 
			else sp.freight_charge end as price_unit
    			
    			,case when sp.state = 'freight_paid' then sp.freight_balance else 0 end as freight_paid
    			,case when sp.state = 'freight_paid' then  sp.freight_balance else 0 end as freight_balance
    			,sm.rejected_qty
    			,case when i.freight=false then sm.deduction_amt else sp.freight_deduction end as deduction_amt
    			,(sm.rejected_qty * sm.price_unit + sm.deduction_amt) as ded_amount
    			, rp.ref
    		from account_invoice i 
    		inner join supp_delivery_invoice_rel dl on dl.invoice_id = i.id 
    		inner join stock_picking sp on sp.id = dl.del_ord_id
    		inner join res_partner rp on rp.id = sp.partner_id
    		inner join stock_move sm on sm.picking_id = sp.id
    		inner join product_product p on p.id = sm.product_id
    		and sp.state in ('done','freight_paid') 
    		and i.id = inv_id)

    		union all

		   (select 
			 sp.name as name 
			,i.date_invoice as date
			,p.default_code
			,'' as truck_no
			,al.quantity as product_qty
			,al.quantity  as unloaded_qty
			,k.product_price as price_unit
			, 0 as freight_paid
			,0 as freight_balance
			, 0 as rejected_qty
			,0 as deduction_amt
			,0 as ded_amount
			,rp.ref
		from account_invoice i
		inner join incoming_shipment_invoice_rel isr on isr.invoice_id = i.id
		inner join stock_picking sp on sp.id = isr.in_shipment_id
		inner join account_invoice_line al on al.invoice_id = i.id
		inner join res_partner rp on rp.id = i.partner_id
		inner join product_product p on p.id = al.product_id
		inner join product_supplierinfo ps on ps.product_id = p.id 
		inner join kw_product_price k on k.supp_info_id = ps.id
		and i.date_invoice = st_date::date 
		and k.ef_date < st_date::date 
		and i.origin= 'in' 
		and i.partner_id = sup
		and i.id = inv_id)
    		)data  
         );
    
       -- inserting the opening amount and closing amount 		
           Insert into tmp_amount(id,amount)
    	/*(SELECT nextval('pay_seq') as id,
           case when sum(debit - credit)>0 then sum(debit - credit)  else 0 end as amount 
    	FROM account_move_line aml
    	INNER JOIN res_partner rp ON rp.id = aml.partner_id
    	WHERE aml.partner_id = sup
    	AND aml.account_id =
    		(SELECT substr(value_reference,17)::integer
    		FROM ir_property
    		WHERE name = 'property_account_payable'
    		AND res_id = 'res.partner,' || sup)
    	AND aml.date <= st_date::date)
    
    	union all*/
    	(
    	select nextval('pay_seq') as id,
    	case when amount >0 then amount else 0 end as amount from account_voucher where date = st_date and freight =false
    	and partner_id = sup 
    	);
    
    	
    	select count(id) into amount_count from tmp_amount;
    	select count(id) into delivery_count from tmp_del_orders;
    	
    
    	
    	
    	--for calculation opening and closing balance
            FOR rec IN select id, amount_payable,opening_balance from tmp_del_orders LOOP
                select amount into open_bal from tmp_amount where id = i;
    
                if open_bal is null then open_bal := 0;end if;
                
                curr_closebal = prev_closebal + rec.amount_payable - open_bal;
    
    	    update tmp_del_orders set opening_balance = open_bal, 
    				      closing_balance = curr_closebal
    	    where id = rec.id;
    	    prev_closebal = curr_closebal;
    	    i := i +1;
    	    
    	END LOOP;
    
    	
    	-- if amount paid is greather than the delivery order lines then insert amount
    	if amount_count > delivery_count then
    	
    		FOR rec IN select id, amount from tmp_amount where id >= i LOOP
    		    select amount into open_bal from tmp_amount where id = i;
    
    		    if open_bal is null then open_bal := 0;end if;
    		    
    		    curr_closebal = prev_closebal - open_bal;
    
    		   
    		    insert into tmp_del_orders(id,opening_balance, closing_balance)
    			( select nextval('do_seq') as id 
    			       , open_bal
    			       , curr_closebal
    			);
    		    prev_closebal = curr_closebal;
    		    i := i +1;
    		    
    		END LOOP;
    		
    	
    	end if;
    	
             FOR r IN select * from tmp_del_orders LOOP
    	return next r;          
        END LOOP;
        
        RETURN;  
    END 
    
    $BODY$
  LANGUAGE plpgsql VOLATILE;
    
 -- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- 				FUNCTION:Purchase summary for Transit records
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

drop type if exists transit_data cascade;

create type transit_data as (id int,   
	  name varchar(50), 
	  date date,
	  default_code varchar(50),
	  truck_no varchar(100),
	  product_qty numeric,
	  price_unit numeric,
	  amount numeric,
	  freight_paid numeric,
	  amount_payable numeric,
	  grand_total_payable numeric,
	  company varchar(100)
	  ); 
	  
	  
   CREATE OR REPLACE FUNCTION purchase_smry_transit(start_dt date, sup integer)
     RETURNS SETOF transit_data AS
      $BODY$
    DECLARE
       r transit_data%rowtype;
       st_date timestamp;
       open_bal numeric(16,2) :=0; 
       curr_closebal numeric(16,2) :=0;
       prev_closebal numeric(16,2) :=0;
       delivery_count integer;
       amount_count integer;
       rec record;
       i integer :=1;
       
    BEGIN
    	st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh:mi:ss');
    
    
    	DROP SEQUENCE if exists do_seq1;
    	CREATE TEMP sequence do_seq1;
    
    	DROP SEQUENCE if exists pay_seq1;
    	CREATE TEMP sequence pay_seq1;
    	
    	DROP TABLE if exists tmp_transit_orders;
    	CREATE TEMP TABLE tmp_transit_orders
    		( id int,   
    		  name varchar(50), 
    		  date date,
    		  default_code varchar(50),
    		  truck_no varchar(100),
    		  product_qty numeric,
    		  price_unit numeric,
    		  amount numeric,
    		  freight_paid numeric,
    		  amount_payable numeric,
    		  grand_total_payable numeric,
    		  company varchar(100)
    		  
    		)
    	ON COMMIT DROP;
    
    	
         INSERT INTO tmp_transit_orders(id, name, date, default_code, truck_no,product_qty, price_unit,amount,freight_paid,amount_payable,company)
         ( SELECT nextval('do_seq1') as id 
    	 , data.name
             , data.date
             , data.default_code
             , data.truck_no  
             , data.product_qty
             , data.price_unit 
             , (data.price_unit * data.qty) as amount 
             , data.freight_paid
             , ((data.price_unit * data.qty) - data.freight_paid) as amount_payable
             , data.ref
              FROM
    		(     select
    				sp.name
    				,sp.date 
    				,p.default_code
    				,sp.truck_no
    				,sm.product_qty
    				,case when (select k.product_price from kw_product_price k 
					inner join product_supplierinfo ps on ps.id = k.supp_info_id
					where ps.product_id = sm.product_id and ps.name = sup  and k.ef_date < st_date::date order by k.ef_date desc limit 1) > 0 then 
					(select k.product_price from kw_product_price k 
					inner join product_supplierinfo ps on ps.id = k.supp_info_id
					where ps.product_id = sm.product_id and ps.name = sup  and k.ef_date < st_date::date order by k.ef_date desc limit 1)
					else
					pt.list_price end
					as price_unit
    				,(sm.product_qty) as qty
    				,(sp.freight_charge * sm.product_qty) as freight_paid
    				--,((sm.product_qty * sm.price_unit) - case when sp.freight_balance>0 then sp.freight_balance else 0 end  ) as amount_payable
    				, rp.ref
    				,pt.list_price
    			from stock_picking sp
    			inner join stock_move sm on sm.picking_id = sp.id
    			inner join res_partner rp on rp.id = sp.partner_id
    			inner join product_product p on p.id = sm.product_id
    			inner join product_template pt on pt.id = product_tmpl_id
    			and sp.state = 'in_transit'
    			and sp.date::date = st_date::date
    			and sp.paying_agent_id = sup
    		)data 
    			
    			
    	);
    	
    	
    	--for calculation Grand Total Payable
            FOR rec IN select id, amount_payable from tmp_transit_orders order by name LOOP
            
                curr_closebal = prev_closebal + rec.amount_payable;
    	    update tmp_transit_orders set grand_total_payable = curr_closebal
    	    where id = rec.id;
    	    prev_closebal = curr_closebal;
    	    i := i +1;
    	    
    	END LOOP;
    	
    	
             FOR r IN select * from tmp_transit_orders LOOP
    	return next r;          
        END LOOP;
        
        RETURN;  
    END 
    
    $BODY$
      LANGUAGE 'plpgsql' VOLATILE
      COST 100;
	  
	
 -- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
-- 				FUNCTION  :  Facilitator Estimate
-- ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

﻿﻿drop type if exists est_type cascade;

create type est_type as (
		  id integer,
		  end_date date, 
		  partner varchar(128), 
		  partner_id integer,
		  state_name varchar(128),
		  debit numeric,
		  credit numeric,
		  balance numeric
	  ); 
 drop function if exists facilitator_balance(start_dt date, sup integer, part_id integer);

CREATE OR REPLACE FUNCTION facilitator_balance(start_dt date, part_state integer, part_id integer)
  RETURNS SETOF est_type AS
  $BODY$
    DECLARE
       r est_type%rowtype;
       fy_st_date timestamp;

    BEGIN
	fy_st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh24:mi:ss');

	DROP SEQUENCE if exists bal_seq;
    	CREATE TEMP sequence bal_seq;

	DROP TABLE if exists temp_cycle	;
    	CREATE TEMP TABLE temp_cycle(
		id integer,
		st_date date,
		end_date date,
		partner_id integer);
		

	DROP TABLE if exists partner_balance;
	CREATE TEMP TABLE partner_balance(
		  id  integer,
		  end_date date,
		  partner varchar(128), 
		  partner_id integer,
		  state_name varchar(128),
		  debit numeric,
		  credit numeric,
		  balance numeric);
		  


	insert into temp_cycle(id,st_date,end_date,partner_id)
	(	select 
			1 as id
			, bc1.st_date 
			, bc1.end_date
			, bc1.partner_id
		from billing_cycle bc1
		inner join res_partner rp1 on rp1.id = bc1.partner_id
		left outer join res_country_state rcs on rcs.id = rp1.state_id
		where bc1.id in
			(
				select 
				bc.id
				from billing_cycle bc 
				inner join res_partner rs on rs.id = bc.partner_id
				where bc.partner_id in (rp1.id)
				order by end_date desc limit 1
			)
		and case when part_state >0 then rcs.id = part_state else rcs.id >0 end
		and case when part_id >0 then rp1.id = part_id else rp1.id >0 end
		and rp1.name not ilike '%Kingswood%'
		and rp1.supplier is true
		and not rp1.handling_charges
		
	);


	INSERT INTO partner_balance(id, end_date, partner,  partner_id, state_name,debit, credit, balance)
		(select 
			  nextval('bal_seq') as id
			, zz.end_date
			, zz.partner_name
			, zz.partner
			, zz.state_name
			, sum(zz.debit) as debit
			, sum(zz.credit) as credit
			, (sum(debit) - sum(credit)) as balance 

		from
		(
		select
			b.end_date,
			b.partner_id as partner,
			b.partner_name,
			b.state_name,
			fy_st_date::date as date,
			'TO OPENING BALANCE' AS name,
			 case when (sum(b.bal) + sum(freight))>0 then 
			 abs(sum(b.bal) + sum(freight)) else 0 end  AS debit,

			 case when (sum(b.bal) + sum(freight))>0 then 0 
			 else abs(sum(b.bal) + sum(freight)) end AS credit
			
			from
			(select
				tc.end_date,		
				aml.partner_id,
				rp.name as partner_name,
				rs.name as state_name,
				case when sum(debit-credit) is null then 0 else  sum(debit-credit) end as bal,
				0 as freight
			from account_move_line aml
			inner join res_partner rp on aml.partner_id = rp.id
			inner join res_country_state rs on rs.id = rp.state_id
			inner join temp_cycle tc on tc.partner_id = rp.id
			AND aml.account_id in
				    ((SELECT substr(value_reference,17)::integer
				     FROM ir_property
				     WHERE name = 'property_account_payable'
				     AND res_id = 'res.partner,' || rp.id),rp.account_pay)
			and aml.date<tc.st_date::date
			and aml.date>=fy_st_date::date --fiscal_year
			and aml.partner_id = tc.partner_id
			--excluding freight advances
			and aml.ref not like 'DC%'
			group by aml.partner_id, rp.name, rs.name,tc.end_date
			--order by aml.partner_id, rp.name, rs.name
			

			union all

			select 
					tc3.end_date,
					sp.paying_agent_id as partner_id,
					rp.name as partner_name,
					rcs.name as state_name,
					0 as bal,
					case when sum(freight_balance)>0 then sum(freight_balance) else 0 end  as freight 
				from stock_picking sp
				inner join account_voucher a on sp.name = a.reference
				inner join temp_cycle tc3 on a.partner_id = tc3.partner_id
				inner join res_partner rp on rp.id = a.partner_id
				left outer join res_country_state rcs on rcs.id = rp.state_id
				where sp.sup_invoice is true and sp.state='freight_paid' 
				and sp.id in 
					(select distinct del_ord_id from supp_delivery_invoice_rel sl
						inner join account_invoice ai1 on ai1.id = sl.invoice_id
						inner join temp_cycle tc2 on tc2.partner_id = ai1.partner_id
						where invoice_id in 
						(select
							ai.id 
						from account_invoice ai
						inner join temp_cycle tc1 on tc1.partner_id = ai.partner_id
						where ai.partner_id = tc1.partner_id 
						--and ai.partner_id = 1541
						and ai.date_invoice <tc1.st_date::date 
						and state not in ('draft','cancel') 
						and type = 'in_invoice'
						)
						and ai1.partner_id = tc2.partner_id
					)
						and a.partner_id = tc3.partner_id 

				group by sp.paying_agent_id, rp.name, rcs.name ,tc3.end_date	
			)b

				
			
			
			group by b.partner_id, b.partner_name,b.state_name,b.end_date	
			

		union all
			

		(select
			x.end_date,
			partner as partner,
			x.partner_name,
			x.state_name,
			x.date_invoice, 
			x.name AS name,
			sum(x.debit) as debit,
			sum(x.credit) as credit
			from
		(select  
			tc.end_date,
			rp1.id as partner,
			rp1.name as partner_name,
			rs.name as state_name,
			v1.date as date_invoice,
			case when v1.reference is null then number else v1.reference end as name,
			v1.amount as debit,
			0 as credit 
		from account_voucher v1
		inner join res_partner rp1 on rp1.id = v1.partner_id
		inner join res_country_state rs on rs.id = rp1.state_id
		inner join temp_cycle tc on tc.partner_id = rp1.id
		where v1.type in ('payment','sale')
		and v1.freight =false 
		and amount >0 
		and v1.date between tc.st_date::date and tc.end_date::date

		union all

		select 
			tc.end_date,
			rp2.id as partner,
			rp2.name as partner_name,
			rs.name as state_name,
			v2.date,
			case when reference is null then number else reference end as name,
			0 as debit,
			amount as credit	
		from account_voucher v2
		inner join res_partner rp2 on rp2.id = v2.partner_id
		left outer join res_country_state rs on rs.id = rp2.state_id
		inner join temp_cycle tc on tc.partner_id = rp2.id
		where v2.type in ('purchase','receipt')
		and v2.freight =false and v2.partner_id = tc.partner_id 
		and amount >0 
		and v2.date between tc.st_date::date and tc.end_date::date

		union all

		--to get refund which are not in line
		select 
			tc.end_date,
			i.partner_id as partner,
			rp3.name as partner_name,
			rs.name as state_name,
			i.date_invoice,
			'Refund' || '-' || (case when reference is null then i.origin else i.reference end) as name,
			i.amount_total as debit,
			0 as credit
		from account_invoice i 
		inner join supp_delivery_invoice_rel sl
		on sl.invoice_id = i.id
		inner join res_partner rp3 on rp3.id = i.partner_id
		inner join res_country_state rs on rs.id = rp3.state_id
		inner join temp_cycle tc on tc.partner_id = rp3.id
		where i.type = 'in_refund' and i.state = 'open'
		and sl.del_ord_id not in (select sp.id from stock_picking sp 
					left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
					left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
					inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
					inner join temp_cycle tc1 on tc1.partner_id = i.partner_id
					and  i.state in ('open','paid')
					and i.date_invoice between tc1.st_date::date and tc1.end_date::date
					and i.type = 'in_invoice'
				)
		and i.date_invoice between tc.st_date::date and tc.end_date::date

		union all
		--to get refund invoice with out DO
		select 
			tc.end_date,
			i.partner_id as partner,
			rp4.name as partner_name,
			rs.name as state_name,
			i.date_invoice,
			'Refund' || '-' || (case when reference is null then i.number else i.reference end) as name,
			i.amount_total as debit,
			0 as credit
		from account_invoice i 
		left outer join supp_delivery_invoice_rel sl
		on sl.invoice_id = i.id
		inner join res_partner rp4 on rp4.id = i.partner_id
		inner join res_country_state rs on rs.id = rp4.state_id
		inner join temp_cycle tc on tc.partner_id = rp4.id
		where i.type = 'in_refund' and i.state not in ('draft','cancel')
		and i.date_invoice between tc.st_date::date and tc.end_date::date
		and sl.del_ord_id is null
		)x
		group by x.partner, x.partner_name, x.state_name, x.date_invoice, x.name,x.end_date
		order by x.date_invoice)


		union all
			(
			select 
			  xi.end_date
			, xi.partner_id as partner
			, xi.name as partner_name
			, xi.state_name
			, now()::date as date_invoice
			,'LESS RECEIPTS' AS name 
			,'0' AS debit
			,sum(xi.unloaded_qty * xi.price_unit)-
			(case when sum(yi.amount) is null then 0 else sum (yi.amount)end)-
			(case when sum(xi.ded_amt) is null then 0 else sum(xi.ded_amt) end) as credit
			from 
		(SELECT distinct sp.name as dc_no
				,sp.date
				, tc.end_date
				, rp.name
				, rs.name as state_name
				,p.default_code
				,i.partner_id
				,case when sm.deduction_amt>0 then sm.deduction_amt else 0 end as ded_amt
			,case when sp.type = 'out' then (case when sm.unloaded_qty >0 then sm.unloaded_qty else sm.cft1+sm.cft2 end)
				else sm.product_qty end as unloaded_qty
			,case when sm.rejected_qty>0 then sm.rejected_qty else 0 end as rejected_qty  
			,case when fln.price_unit is not null then ln.price_unit + fln.price_unit else  ln.price_unit end as price_unit
			,case when sm.rejected_qty >0 then sm.rejected_qty else 0 end
			from stock_picking sp 
			left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
			left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
			inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
			inner join stock_move sm on
			sm.picking_id = sp.id
			inner join product_product p on
			p.id = sm.product_id
			inner join stock_location sl on sl.id = sm.location_dest_id
			inner join res_partner rp on
			case when sp.type = 'out' then rp.id = sp.paying_agent_id else rp.id = sp.partner_id end
			inner join res_country_state rs on rs.id = rp.state_id
			inner join temp_cycle tc on tc.partner_id = rp.id
			where i.date_invoice between tc.st_date::date and  tc.end_date::date
			and i.partner_id = tc.partner_id
			and  i.state in ('open','paid')
			and sp.state in ('done','freight_paid')
			 
			order by p.default_code,i.partner_id
			)xi
			left outer join
			(select  a.amount  as amount
				,a.reference from stock_picking sp
				left join account_voucher a  on
				a.reference = sp.name
				left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
				left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
				inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
				inner join temp_cycle tc on tc.partner_id = i.partner_id
				where a.freight = true
				and  i.state in ('open','paid') 
				and i.date_invoice between tc.st_date::date and  tc.end_date::date
				group by a.reference,a.amount
				order by a.reference
			)yi on xi.dc_no = yi.reference
			group by  xi.name,xi.state_name,xi.partner_id,xi.end_date
			)
			)zz
			
			group by zz.partner_name, zz.state_name,zz.partner,zz.end_date
			order by zz.state_name, zz.partner_name
		);
	FOR r IN select * from partner_balance LOOP
		return next r;          
        END LOOP;
        
        RETURN;  
    END 
    
    $BODY$
  LANGUAGE plpgsql VOLATILE;
  
  
  --~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  --                       Faciliator Estimate and Balance 
  --~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  
-- drop type if exists est_bal_type cascade;
--
-- create type est_bal_type as (
-- 		  id integer,
-- 		  end_date date,
-- 		  partner varchar(128),
-- 		  partner_id integer,
-- 		  state_name varchar(128),
-- 		  debit numeric,
-- 		  credit numeric,
-- 		  balance numeric,
-- 		  payments numeric,
-- 		  receipts numeric,
-- 		  estimate numeric
--
-- 	  );
--
-- drop function if exists facilitator_estimate(date, integer, integer);
-- CREATE OR REPLACE FUNCTION facilitator_estimate(start_dt date, part_state integer, part_id integer)
--   RETURNS SETOF est_bal_type AS
--   $BODY$
--     DECLARE
--        r est_bal_type%rowtype;
--        fy_st_date timestamp;
--
--     BEGIN
-- 	fy_st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh24:mi:ss');
--
-- 	DROP SEQUENCE if exists est_seq;
--     	CREATE TEMP sequence est_seq;
--
-- 	DROP TABLE if exists tmp_cycle	;
--     	CREATE TEMP TABLE tmp_cycle(
-- 		id integer,
-- 		st_date date,
-- 		end_date date,
-- 		partner_id integer);
--
--
-- 	DROP TABLE if exists partner_estimate;
-- 	CREATE TEMP TABLE partner_estimate(
-- 		  id  integer,
-- 		  end_date date,
-- 		  partner varchar(128),
-- 		  partner_id integer,
-- 		  state_name varchar(128),
-- 		  debit numeric,
-- 		  credit numeric,
-- 		  balance numeric,
-- 		  payments numeric,
-- 		  receipts numeric,
-- 		  estimate numeric
-- 		  );
--
-- 	insert into tmp_cycle(id,st_date,end_date,partner_id)
-- 	(	select
-- 			1 as id
-- 			, bc1.st_date
-- 			, bc1.end_date
-- 			, bc1.partner_id
-- 		from billing_cycle bc1
-- 		inner join res_partner rp1 on rp1.id = bc1.partner_id
-- 		left outer join res_country_state rcs on rcs.id = rp1.state_id
-- 		where bc1.id in
-- 			(
-- 				select
-- 				bc.id
-- 				from billing_cycle bc
-- 				inner join res_partner rs on rs.id = bc.partner_id
-- 				where bc.partner_id in (rp1.id)
-- 				order by end_date desc limit 1
-- 			)
-- 		and case when part_state >0 then rcs.id = part_state else rcs.id >0 end
-- 		and case when part_id >0 then rp1.id = part_id else rp1.id >0 end
-- 		and rp1.name not ilike '%Kingswood%'
-- 		and rp1.supplier is true
-- 		and not rp1.handling_charges
--
-- 	);
--
--
--
-- INSERT INTO partner_estimate(id, end_date, partner,  partner_id, state_name,debit, credit, balance, payments, receipts, estimate)
-- (
--
-- select
-- 		  nextval('est_seq') as id
-- 		, zz.end_date
-- 		, zz.partner_name
-- 		, zz.partner
-- 		, zz.state_name
-- 		, sum(zz.debit) as debit
-- 		, sum(zz.credit) as credit
-- 		, (sum(debit) - sum(credit)) as balance
-- 		, case when z.payments is not null then z.payments else 0 end as payments
-- 		, case when z.receipt is not null then z.receipt else 0 end as receipts
-- 		, case when z.estimate is not null then z.estimate else 0 end as estimate
-- 		--, z.partner_id
--
-- 	from
-- 	(
-- 	select
-- 		b.end_date,
-- 		b.partner_id as partner,
-- 		b.partner_name,
-- 		b.state_name,
-- 		'2014-04-01'::date as date,
-- 		'TO OPENING BALANCE' AS name,
-- 		 case when (sum(b.bal) + sum(freight))>0 then
-- 		 abs(sum(b.bal) + sum(freight)) else 0 end  AS debit,
--
-- 		 case when (sum(b.bal) + sum(freight))>0 then 0
-- 		 else abs(sum(b.bal) + sum(freight)) end AS credit
--
-- 		from
-- 		(select
-- 			tc.end_date,
-- 			aml.partner_id,
-- 			rp.name as partner_name,
-- 			rs.name as state_name,
-- 			case when sum(debit-credit) is null then 0 else  sum(debit-credit) end as bal,
-- 			0 as freight
-- 		from account_move_line aml
-- 		inner join res_partner rp on aml.partner_id = rp.id
-- 		inner join res_country_state rs on rs.id = rp.state_id
-- 		inner join tmp_cycle tc on tc.partner_id = rp.id
-- 		AND aml.account_id in
-- 			    ((SELECT substr(value_reference,17)::integer
-- 			     FROM ir_property
-- 			     WHERE name = 'property_account_payable'
-- 			     AND res_id = 'res.partner,' || rp.id),rp.account_pay)
-- 		and aml.date<tc.st_date::date
-- 		and aml.date>='2014-04-01'::date --fiscal_year
-- 		and aml.partner_id = tc.partner_id
-- 		--excluding freight advances
-- 		and aml.ref not like 'DC%'
-- 		group by aml.partner_id, rp.name, rs.name,tc.end_date
-- 		--order by aml.partner_id, rp.name, rs.name
--
--
-- 		union all
--
-- 		select
-- 				tc3.end_date,
-- 				sp.paying_agent_id as partner_id,
-- 				rp.name as partner_name,
-- 				rcs.name as state_name,
-- 				0 as bal,
-- 				case when sum(freight_balance)>0 then sum(freight_balance) else 0 end  as freight
-- 			from stock_picking sp
-- 			inner join account_voucher a on sp.name = a.reference
-- 			inner join tmp_cycle tc3 on a.partner_id = tc3.partner_id
-- 			inner join res_partner rp on rp.id = a.partner_id
-- 			left outer join res_country_state rcs on rcs.id = rp.state_id
-- 			where sp.sup_invoice is true and sp.state='freight_paid'
-- 			and sp.id in
-- 				(select distinct del_ord_id from supp_delivery_invoice_rel sl
-- 					inner join account_invoice ai1 on ai1.id = sl.invoice_id
-- 					inner join tmp_cycle tc2 on tc2.partner_id = ai1.partner_id
-- 					where invoice_id in
-- 					(select
-- 						ai.id
-- 					from account_invoice ai
-- 					inner join tmp_cycle tc1 on tc1.partner_id = ai.partner_id
-- 					where ai.partner_id = tc1.partner_id
-- 					--and ai.partner_id = 1541
-- 					and ai.date_invoice <tc1.st_date::date
-- 					and state not in ('draft','cancel')
-- 					and type = 'in_invoice'
-- 					)
-- 					and ai1.partner_id = tc2.partner_id
-- 				)
-- 					and a.partner_id = tc3.partner_id
--
-- 			group by sp.paying_agent_id, rp.name, rcs.name ,tc3.end_date
-- 		)b
--
-- 		group by b.partner_id, b.partner_name,b.state_name,b.end_date
--
--
-- 	union all
--
--
-- 	(select
-- 		x.end_date,
-- 		partner as partner,
-- 		x.partner_name,
-- 		x.state_name,
-- 		x.date_invoice,
-- 		x.name AS name,
-- 		sum(x.debit) as debit,
-- 		sum(x.credit) as credit
-- 		from
-- 	(select
-- 		tc.end_date,
-- 		rp1.id as partner,
-- 		rp1.name as partner_name,
-- 		rs.name as state_name,
-- 		v1.date as date_invoice,
-- 		case when v1.reference is null then number else v1.reference end as name,
-- 		v1.amount as debit,
-- 		0 as credit
-- 	from account_voucher v1
-- 	inner join res_partner rp1 on rp1.id = v1.partner_id
-- 	inner join res_country_state rs on rs.id = rp1.state_id
-- 	inner join tmp_cycle tc on tc.partner_id = rp1.id
-- 	where v1.type in ('payment','sale')
-- 	and v1.freight =false
-- 	and amount >0
-- 	and v1.date between tc.st_date::date and tc.end_date::date
--
-- 	union all
--
-- 	select
-- 		tc.end_date,
-- 		rp2.id as partner,
-- 		rp2.name as partner_name,
-- 		rs.name as state_name,
-- 		v2.date,
-- 		case when reference is null then number else reference end as name,
-- 		0 as debit,
-- 		amount as credit
-- 	from account_voucher v2
-- 	inner join res_partner rp2 on rp2.id = v2.partner_id
-- 	left outer join res_country_state rs on rs.id = rp2.state_id
-- 	inner join tmp_cycle tc on tc.partner_id = rp2.id
-- 	where v2.type in ('purchase','receipt')
-- 	and v2.freight =false and v2.partner_id = tc.partner_id
-- 	and amount >0
-- 	and v2.date between tc.st_date::date and tc.end_date::date
--
-- 	union all
--
-- 	--to get refund which are not in line
-- 	select
-- 		tc.end_date,
-- 		i.partner_id as partner,
-- 		rp3.name as partner_name,
-- 		rs.name as state_name,
-- 		i.date_invoice,
-- 		'Refund' || '-' || (case when reference is null then i.origin else i.reference end) as name,
-- 		i.amount_total as debit,
-- 		0 as credit
-- 	from account_invoice i
-- 	inner join supp_delivery_invoice_rel sl
-- 	on sl.invoice_id = i.id
-- 	inner join res_partner rp3 on rp3.id = i.partner_id
-- 	inner join res_country_state rs on rs.id = rp3.state_id
-- 	inner join tmp_cycle tc on tc.partner_id = rp3.id
-- 	where i.type = 'in_refund' and i.state = 'open'
-- 	and sl.del_ord_id not in (select sp.id from stock_picking sp
-- 				left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
-- 				left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
-- 				inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
-- 				inner join tmp_cycle tc1 on tc1.partner_id = i.partner_id
-- 				and  i.state in ('open','paid')
-- 				and i.date_invoice between tc1.st_date::date and tc1.end_date::date
-- 				and i.type = 'in_invoice'
-- 			)
-- 	and i.date_invoice between tc.st_date::date and tc.end_date::date
--
-- 	union all
-- 	--to get refund invoice with out DO
-- 	select
-- 		tc.end_date,
-- 		i.partner_id as partner,
-- 		rp4.name as partner_name,
-- 		rs.name as state_name,
-- 		i.date_invoice,
-- 		'Refund' || '-' || (case when reference is null then i.number else i.reference end) as name,
-- 		i.amount_total as debit,
-- 		0 as credit
-- 	from account_invoice i
-- 	left outer join supp_delivery_invoice_rel sl
-- 	on sl.invoice_id = i.id
-- 	inner join res_partner rp4 on rp4.id = i.partner_id
-- 	inner join res_country_state rs on rs.id = rp4.state_id
-- 	inner join tmp_cycle tc on tc.partner_id = rp4.id
-- 	where i.type = 'in_refund' and i.state not in ('draft','cancel')
-- 	and i.date_invoice between tc.st_date::date and tc.end_date::date
-- 	and sl.del_ord_id is null
-- 	)x
-- 	group by x.partner, x.partner_name, x.state_name, x.date_invoice, x.name,x.end_date
-- 	order by x.date_invoice)
--
--
-- 	union all
-- 		(
-- 		select
-- 		  xi.end_date
-- 		, xi.partner_id as partner
-- 		, xi.name as partner_name
-- 		, xi.state_name
-- 		, now()::date as date_invoice
-- 		,'LESS RECEIPTS' AS name
-- 		,'0' AS debit
-- 		,sum(xi.unloaded_qty * xi.price_unit)-
-- 		(case when sum(yi.amount) is null then 0 else sum (yi.amount)end)-
-- 		(case when sum(xi.ded_amt) is null then 0 else sum(xi.ded_amt) end) as credit
-- 		from
-- 	(SELECT distinct sp.name as dc_no
-- 			,sp.date
-- 			, tc.end_date
-- 			, rp.name
-- 			, rs.name as state_name
-- 			,p.default_code
-- 			,i.partner_id
-- 			,case when sm.deduction_amt>0 then sm.deduction_amt else 0 end as ded_amt
-- 		,case when sp.type = 'out' then (case when sm.unloaded_qty >0 then sm.unloaded_qty else sm.cft1+sm.cft2 end)
-- 			else sm.product_qty end as unloaded_qty
-- 		,case when sm.rejected_qty>0 then sm.rejected_qty else 0 end as rejected_qty
-- 		,case when fln.price_unit is not null then ln.price_unit + fln.price_unit else  ln.price_unit end as price_unit
-- 		,case when sm.rejected_qty >0 then sm.rejected_qty else 0 end
-- 		from stock_picking sp
-- 		left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
-- 		left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
-- 		inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
-- 		inner join stock_move sm on
-- 		sm.picking_id = sp.id
-- 		inner join product_product p on
-- 		p.id = sm.product_id
-- 		inner join stock_location sl on sl.id = sm.location_dest_id
-- 		inner join res_partner rp on
-- 		case when sp.type = 'out' then rp.id = sp.paying_agent_id else rp.id = sp.partner_id end
-- 		inner join res_country_state rs on rs.id = rp.state_id
-- 		inner join tmp_cycle tc on tc.partner_id = rp.id
-- 		where i.date_invoice between tc.st_date::date and  tc.end_date::date
-- 		and i.partner_id = tc.partner_id
-- 		and  i.state in ('open','paid')
-- 		and sp.state in ('done','freight_paid')
--
-- 		order by p.default_code,i.partner_id
-- 		)xi
-- 		left outer join
-- 		(select  a.amount  as amount
-- 			,a.reference from stock_picking sp
-- 			left join account_voucher a  on
-- 			a.reference = sp.name
-- 			left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
-- 			left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
-- 			inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
-- 			inner join tmp_cycle tc on tc.partner_id = i.partner_id
-- 			where a.freight = true
-- 			and  i.state in ('open','paid')
-- 			and i.date_invoice between tc.st_date::date and  tc.end_date::date
-- 			group by a.reference,a.amount
-- 			order by a.reference
-- 		)yi on xi.dc_no = yi.reference
-- 		group by  xi.name,xi.state_name,xi.partner_id,xi.end_date
-- 		)
-- 		)zz
--
--
-- 	left outer join
--
--
-- --- Estimate
--
-- 	(select
-- 		ab.partner_id
-- 		, ab.supp_name
-- 		, sum(ab.debit) as payments
--
-- 		, sum(ab.credit) as receipt
-- 		, sum(ab.estimated_amt) + sum(ab.credit) as estimate
-- 	from
-- 	(
-- 		(select
-- 			a.partner_id
-- 			, a.supp_name
-- 			, 0 as debit
-- 			, 0 as credit
-- 			-- substracting the freight paid amount
-- 			, case when sum(a.price_unit) is not null then sum((a.price_unit * a.qty)+a.freight_balance) - sum(fre_total)
-- 			else sum((a.line_price * a.qty)+ a.freight_balance) - sum(fre_total) end as estimated_amt
--
-- 			from
-- 			(
-- 				(	select sp.name as dc_no
-- 					, sp.date
-- 					, sp.state
-- 					--, sm.unloaded_qty
-- 					, sp.paying_agent_id as partner_id
-- 					, case when sp.state = 'in_transit' then sm.product_qty else sm.unloaded_qty end as qty
-- 					, case when sp.state != 'freight_paid' then
-- 						case when (sm.product_qty * sp.freight_charge) is not null then  (sm.product_qty * sp.freight_charge)
-- 						else 0 end else 0 end as fre_total
-- 					, (	select
-- 							case when kw.product_price is not null
-- 							then kw.product_price + (case when kw.transport_price is not null then kw.transport_price else 0 end)  else 0 end
-- 						from product_supplierinfo ps
-- 						inner join kw_product_price kw on ps.id = kw.supp_info_id
-- 						and ps.name = sp.paying_agent_id
-- 						and ps.customer_id = sp.partner_id
-- 						and ef_date <= sm.delivery_date
-- 						and ps.product_id = sm.product_id
-- 						order by ef_date desc limit 1) as price_unit
--
-- 					, sm.price_unit as line_price
-- 					, case when sp.state = 'freight_paid' then -sp.freight_balance else 0 end as freight_balance
-- 					, rp.name as supp_name
-- 				from stock_picking sp
-- 				inner join stock_move sm on
-- 				sm.picking_id = sp.id
-- 				inner join product_product p on
-- 				p.id = sm.product_id
-- 				inner join res_partner rp on
-- 				rp.id = sp.paying_agent_id
-- 				inner join tmp_cycle tc on tc.partner_id = rp.id
-- 				where sp.create_date::date <=now()::date
-- 				and sp.create_date::date >= (select date_start from account_fiscalyear where date_start <= now()::date and date_stop >=now()::date order by id desc limit 1)
-- 				and sp.state not in ('draft','cancel')
-- 				and invoice_line_id is null
-- 				and finvoice_line_id is null
-- 				AND rp.name not ilike '%Kingswood%'
-- 				and rp.supplier is true and rp.handling_charges is false
-- 				order by sp.paying_agent_id
-- 				)
-- 			union all
-- 			(
-- 			select sp.name as dc_no
-- 				, sp.date
-- 				, sp.state
-- 				, sp.partner_id as partner_id
-- 				, sm.product_qty as qty
-- 				,0 as fre_total
-- 				, (	select
-- 						case when kw.product_price is not null
-- 						then kw.product_price + (case when kw.transport_price is not null then kw.transport_price else 0 end)  else 0 end
-- 					from product_supplierinfo ps
-- 					inner join kw_product_price kw on ps.id = kw.supp_info_id
-- 					and ps.name = sp.partner_id
-- 					and ps.depot = sm.location_dest_id
-- 					and ef_date <= sm.delivery_date
-- 					and ps.product_id = sm.product_id
-- 					order by ef_date desc limit 1) as price_unit
--
-- 				, pt.list_price as line_price
-- 				, 0 as freight_balance
-- 				, rp.name as supp_name
-- 			from stock_picking sp
-- 			inner join stock_move sm on
-- 			sm.picking_id = sp.id
-- 			inner join product_product p on
-- 			p.id = sm.product_id
-- 			inner join product_template pt on
-- 			pt.id = p.product_tmpl_id
-- 			inner join res_partner rp on
-- 			rp.id = sp.partner_id
-- 			inner join tmp_cycle tc on tc.partner_id = rp.id
-- 			where sp.create_date::date <=now()::date
-- 			and sp.create_date::date >= (select date_start from account_fiscalyear where date_start <= now()::date and date_stop >=now()::date order by id desc limit 1)
-- 			and sp.state in ('done')
-- 			and sp.type = 'in'
-- 			and invoice_line_id is null
-- 			and finvoice_line_id is null
-- 			and sp.sup_invoice is false
-- 			AND rp.name not ilike '%Kingswood%'
-- 			and rp.supplier is true and rp.handling_charges is false
-- 			order by sp.partner_id
-- 			)
-- 		)a
-- 		group by a.supp_name,a.partner_id
-- 		order by a.partner_id
--
-- 	)
--
--
-- 	union all
-- 		(
-- 			select
-- 					rp1.id as partner_id,
-- 					rp1.name as supp_name,
-- 					v1.amount as debit,
-- 					0 as credit,
-- 					0 as estimated_amt
-- 				from account_voucher v1
-- 				inner join res_partner rp1 on rp1.id = v1.partner_id
-- 				inner join res_country_state rs on rs.id = rp1.state_id
-- 				inner join tmp_cycle tc on tc.partner_id = rp1.id
-- 				where v1.type in ('payment','sale')
-- 				and v1.freight =false
-- 				and amount >0
-- 				and v1.date > tc.end_date::date and v1.date <=now()::date
-- 		)
--
-- 	union all
-- 		(
-- 		select
-- 					rp1.id as partner_id,
-- 					rp1.name as supp_name,
-- 					v1.amount as debit,
-- 					0 as credit,
-- 					0 as estimated_amt
-- 				from account_voucher v1
-- 				inner join res_partner rp1 on rp1.id = v1.partner_id
-- 				inner join res_country_state rs on rs.id = rp1.state_id
-- 				inner join tmp_cycle tc on tc.partner_id = rp1.id
-- 				where v1.type in ('purchase','receipt')
-- 				and v1.freight =false
-- 				and amount >0
-- 				and v1.date > tc.end_date::date and v1.date <=now()::date
-- 		)
-- 	)ab
-- 	group by ab.supp_name, ab.partner_id
-- 	order by ab.supp_name, ab.partner_id
-- 	)z
-- 	on z.partner_id = zz.partner
--
-- group by zz.partner_name, zz.state_name,zz.partner, zz.end_date, z.receipt, z.payments, z.estimate
-- order by zz.state_name, zz.partner_name
--
-- );
-- 	FOR r IN select * from partner_estimate LOOP
-- 		return next r;
--         END LOOP;
--
--         RETURN;
--     END
--
--     $BODY$
--   LANGUAGE plpgsql VOLATILE;
--
--   select * from facilitator_estimate('2014-04-01', 54, 1545)

  --~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
  --                     Latest Faciliator Estimate and Balance (Estimate Report)
  --~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

drop type if exists est_bal_type cascade;

create type est_bal_type as (
		  id integer,
		  end_date date,
		  partner varchar(128),
		  partner_id integer,
		  state_name varchar(128),
		  debit numeric,
		  credit numeric,
		  balance numeric,
		  payments numeric,
		  receipts numeric,
		  estimate numeric

	  );

drop function if exists facilitator_estimate(date, integer, integer, date);
CREATE OR REPLACE FUNCTION facilitator_estimate(start_dt date, part_state integer, part_id integer, e_date date)
  RETURNS SETOF est_bal_type AS
  $BODY$
    DECLARE
       r est_bal_type%rowtype;
       fy_st_date timestamp;

    BEGIN
	fy_st_date := to_char((start_dt || ' 00:00:00')::timestamp, 'yyyy-mm-dd hh24:mi:ss');

	DROP SEQUENCE if exists est_seq;
    	CREATE TEMP sequence est_seq;

	DROP TABLE if exists tmp_cycle	;
    	CREATE TEMP TABLE tmp_cycle(
		id integer,
		st_date date,
		end_date date,
		partner_id integer);


	DROP TABLE if exists partner_estimate;
	CREATE TEMP TABLE partner_estimate(
		  id  integer,
		  end_date date,
		  partner varchar(128),
		  partner_id integer,
		  state_name varchar(128),
		  debit numeric,
		  credit numeric,
		  balance numeric,
		  payments numeric,
		  receipts numeric,
		  estimate numeric
		  );

	insert into tmp_cycle(id,st_date,end_date,partner_id)
	(	select
			1 as id
			, bc1.st_date
			, bc1.end_date
			, bc1.partner_id
		from billing_cycle bc1
		inner join res_partner rp1 on rp1.id = bc1.partner_id
		left outer join res_country_state rcs on rcs.id = rp1.state_id
		where bc1.id in
			(
				select
				bc.id
				from billing_cycle bc
				inner join res_partner rs on rs.id = bc.partner_id
				where bc.partner_id in (rp1.id)
				order by end_date desc limit 1
			)
		and case when part_state >0 then rcs.id = part_state else rcs.id >0 end
		and case when part_id > 0 then rp1.id in (select id from res_partner where id = part_id
							union all
							select id from res_partner where parent_id = part_id) else rp1.id >0 end
		and rp1.name not ilike '%Kingswood%'
		and rp1.supplier is true
		and not rp1.handling_charges

	);



INSERT INTO partner_estimate(id, end_date, partner,  partner_id, state_name,debit, credit, balance, payments, receipts, estimate)
(

select
		  nextval('est_seq') as id
		, max(end_date) as end_date
		, (select name from res_partner where id = part_id) as partner_name
		, (select id from res_partner where id = part_id) as partner
		, max(zz.state_name) as state_name
		, sum(zz.debit) as debit
		, sum(zz.credit) as credit
		, (sum(debit) - sum(credit)) as balance
		, case when z.payments is not null then z.payments else 0 end as payments
		, case when z.receipt is not null then z.receipt else 0 end as receipts
		, case when z.estimate is not null then z.estimate else 0 end as estimate
		--, z.partner_id

	from
	(
	select
		  e_date as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id )as partner_name
		, max(b.state_name) as state_name
		, '2014-04-01'::date as date
		, 'TO OPENING BALANCE' AS name
		, case when (sum(b.bal) + sum(freight))>0 then
		  abs(sum(b.bal) + sum(freight)) else 0 end  AS debit

		, case when (sum(b.bal) + sum(freight))>0 then 0
		  else abs(sum(b.bal) + sum(freight)) end AS credit

		from
		(select
			  e_date as end_date
			, part_id as partner_id
			, (select name from res_partner where id = part_id )as partner_name
			, min(rs.name) as state_name
			, case when sum(debit-credit) is null then 0 else  sum(debit-credit) end as bal
			, 0 as freight

		from account_move_line aml
		inner join res_partner rp on aml.partner_id = rp.id
		inner join res_country_state rs on rs.id = rp.state_id
		--inner join tmp_cycle tc on tc.partner_id = rp.id

		where aml.account_id in
                            ((SELECT substr(value_reference,17)::integer
                             FROM ir_property
                             WHERE name = 'property_account_payable'
                             AND  split_part(res_id,',',2)::int in (select distinct(partner_id) from tmp_cycle)
                             union all
                             select rp.account_pay
                             union all
                             select id from account_account where name ilike '%GST%'))
                    and aml.date <(select tp.end_date from tmp_cycle tp where partner_id = part_id)::date
                    and aml.date>='2014-04-01'::date
                    and aml.ref not like 'DC/%' and aml.ref not like 'KA/%' and aml.ref not like 'TN/%'
                    and rp.id in (select distinct(partner_id) from tmp_cycle)


		union all

		select
				  e_date as end_date
				, part_id as partner_id
				, (select name from res_partner where id = part_id) as partner_name
				, min(rcs.name) as state_name
				, 0 as bal
				, case when sum(freight_balance)>0 then sum(freight_balance) else 0 end  as freight

			from stock_picking sp
			inner join account_voucher a on sp.name = a.reference
			--inner join tmp_cycle tc3 on a.partner_id = tc3.partner_id
			--inner join res_partner rp on rp.id = a.partner_id
			left outer join res_country_state rcs on rcs.id = (select state_id from res_partner where id = part_id)
			where sp.sup_invoice is true and sp.state='freight_paid'
			and sp.id in
				(select distinct del_ord_id from supp_delivery_invoice_rel sl
					inner join account_invoice ai1 on ai1.id = sl.invoice_id
					inner join tmp_cycle tc2 on tc2.partner_id = ai1.partner_id
					where invoice_id in
					(select
						  distinct(ai.id)

					from account_invoice ai
					inner join tmp_cycle tc1 on tc1.partner_id in (select distinct(partner_id) from tmp_cycle)
					where ai.partner_id in (select distinct(partner_id) from tmp_cycle)

					and ai.date_invoice <st_date::date and state not in ('draft','cancel')
					and type = 'in_invoice'

					)
					and ai1.partner_id in (select distinct(partner_id) from tmp_cycle)

				)
					and a.partner_id in (select distinct(partner_id) from tmp_cycle)

				group by sp.paying_agent_id
		)b




	union all


	(select
		  end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, min(x.state_name) as state_name
		, max(x.date_invoice) as date_invoice
		, max(x.name) AS name
		, sum(x.debit) as debit
		, sum(x.credit) as credit
		from
	(select
		  e_date as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, rs.name as state_name
		, v1.date as date_invoice
		, case when v1.reference is null then number else v1.reference end as name
		, v1.amount as debit
		, 0 as credit

	from account_voucher v1
	--inner join res_partner rp1 on rp1.id = v1.partner_id
	inner join res_country_state rs on rs.id = (select state_id from res_partner where id = part_id)
	--inner join tmp_cycle tc on tc.partner_id = rp1.id
	where v1.type in ('payment','sale') and v1.partner_id in (select distinct(partner_id) from tmp_cycle)
	and v1.freight =false
	and amount >0
	and v1.date between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date

	union all

	select
		  e_date as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, rs.name as state_name
		, v2.date
		, case when reference is null then number else reference end as name
		, 0 as debit
		, amount as credit

	from account_voucher v2
	--inner join res_partner rp2 on rp2.id = v2.partner_id
	left outer join res_country_state rs on rs.id = (select state_id from res_partner where id = part_id)
	--inner join tmp_cycle tc on tc.partner_id = rp2.id
	where v2.type in ('purchase','receipt')
	and v2.freight =false and v2.partner_id in (select distinct(partner_id) from tmp_cycle)
	and amount >0
	and v2.date between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date
	and v2.partner_id in (select distinct(partner_id) from tmp_cycle)

	union all

	--to get refund which are not in line
	select
		  e_date as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, rs.name as state_name
		, i.date_invoice
		, 'Refund' || '-' || (case when reference is null then i.origin else i.reference end) as name
		, i.amount_total as debit
		, 0 as credit
	from account_invoice i
	inner join supp_delivery_invoice_rel sl on sl.invoice_id = i.id
	--inner join res_partner rp3 on rp3.id = i.partner_id
	left outer join res_country_state rs on rs.id = (select state_id from res_partner where id = part_id)
	--inner join tmp_cycle tc on tc.partner_id = rp3.id
	where i.type = 'in_refund' and i.state = 'open'
	and sl.del_ord_id not in (select sp.id from stock_picking sp
				left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
				left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
				inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
				--inner join tmp_cycle tc1 on tc1.partner_id = i.partner_id
				and  i.state in ('open','paid')
				and i.date_invoice between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date
				and i.type = 'in_invoice' and i.partner_id in (select distinct(partner_id) from tmp_cycle )
			)
	and i.date_invoice between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date
	and i.partner_id in (select distinct(partner_id) from tmp_cycle)

	union all
	--to get refund invoice with out DO
	select
		  e_date as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, rs.name as state_name
		, i.date_invoice
		, 'Refund' || '-' || (case when reference is null then i.number else i.reference end) as name
		, i.amount_total as debit
		, 0 as credit
	from account_invoice i
	left outer join supp_delivery_invoice_rel sl on sl.invoice_id = i.id
	--inner join res_partner rp4 on rp4.id = i.partner_id
	inner join res_country_state rs on rs.id = (select state_id from res_partner where id = part_id)
	--inner join tmp_cycle tc on tc.partner_id = rp4.id
	where i.type = 'in_refund' and i.state not in ('draft','cancel')
	and i.date_invoice between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date
	and sl.del_ord_id is null
	and i.partner_id in (select distinct(partner_id) from tmp_cycle)
	)x
	group by x.partner, x.partner_name, x.state_name, x.date_invoice, x.name,x.end_date
	--order by x.date_invoice
	)


	union all
		(
		select
		  max(end_date) as end_date
		, part_id as partner
		, (select name from res_partner where id = part_id) as partner_name
		, max(xi.state_name) as state_name
		, now()::date as date_invoice
		,'LESS RECEIPTS' AS name
		,'0' AS debit
		,sum(xi.unloaded_qty * xi.price_unit)-
		(case when sum(yi.amount) is null then 0 else sum (yi.amount)end)-
		(case when sum(xi.ded_amt) is null then 0 else sum(xi.ded_amt) end) as credit
		from
	(SELECT distinct  sp.name as dc_no
			, sp.date
			, e_date as end_date
			, (select name from res_partner where id = part_id) as name
			, rs.name as state_name
			, p.default_code
			, i.partner_id
			, case when sm.deduction_amt>0 then sm.deduction_amt else 0 end as ded_amt
		,case when sp.type = 'out' then (case when sm.unloaded_qty >0 then sm.unloaded_qty else sm.cft1+sm.cft2 end)
			else sm.product_qty end as unloaded_qty
		,case when sm.rejected_qty>0 then sm.rejected_qty else 0 end as rejected_qty
		,case when fln.price_unit is not null then ln.price_unit + fln.price_unit else  ln.price_unit end as price_unit
		,case when sm.rejected_qty >0 then sm.rejected_qty else 0 end
		from stock_picking sp
		left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
		left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
		inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
		inner join stock_move sm on sm.picking_id = sp.id
		inner join product_product p on p.id = sm.product_id
		inner join stock_location sl on sl.id = sm.location_dest_id
		inner join res_partner rp on case when sp.type = 'out' then rp.id = sp.paying_agent_id else rp.id = sp.partner_id end
		inner join res_country_state rs on rs.id = rp.state_id
		--inner join tmp_cycle tc on tc.partner_id = rp.id
		where i.date_invoice between (select st_date from tmp_cycle where partner_id = part_id)::date and e_date::date
		and i.partner_id in (select distinct(partner_id) from tmp_cycle)
		and  i.state in ('open','paid')
		and sp.state in ('done','freight_paid')
		and i.partner_id in (select distinct(partner_id) from tmp_cycle)

		order by p.default_code,i.partner_id
		)xi
		left outer join
		(select  a.amount  as amount
			,a.reference from stock_picking sp
			left join account_voucher a  on
			a.reference = sp.name
			left outer join account_invoice_line ln on ln.id = sp.invoice_line_id
			left outer join account_invoice_line fln on fln.id = sp.finvoice_line_id
			inner join account_invoice i on i.id in (fln.invoice_id,ln.invoice_id)
			--inner join tmp_cycle tc on tc.partner_id = i.partner_id
			where a.freight = true
			and  i.state in ('open','paid')
			and i.date_invoice between (select st_date from tmp_cycle where partner_id = part_id)::date and  e_date::date
			and i.partner_id in (select distinct(partner_id) from tmp_cycle)

			group by a.reference,a.amount
			order by a.reference
		)yi on xi.dc_no = yi.reference
		group by xi.partner_id
		)
		)zz


	left outer join


--- Estimate

	(select
		  min(ab.partner_id) as partner_id
		, max(ab.supp_name) as supp_name
		, sum(ab.debit) as payments

		, sum(ab.credit) as receipt
		, sum(ab.estimated_amt) + sum(ab.credit) as estimate
	from
	(
		(select
			 min(a.partner_id) as partner_id
			, max(a.supp_name) as supp_name
			, 0 as debit
			, 0 as credit
			-- substracting the freight paid amount
			, case when sum(a.price_unit) is not null then sum((a.price_unit * a.qty)+a.freight_balance) - sum(fre_total)
			else sum((a.line_price * a.qty)+ a.freight_balance) - sum(fre_total) end as estimated_amt

			from
			(
				(	select sp.name as dc_no
					, sp.date
					, sp.state
					--, sm.unloaded_qty
					, sp.paying_agent_id as partner_id
					, case when sp.state = 'in_transit' then sm.product_qty else sm.unloaded_qty end as qty
					, case when sp.state != 'freight_paid' then
						case when (sm.product_qty * sp.freight_charge) is not null then  (sm.product_qty * sp.freight_charge)
						else 0 end else 0 end as fre_total
					, (	select
							case when kw.product_price is not null
							then kw.product_price + (case when kw.transport_price is not null then kw.transport_price else 0 end)  else 0 end
						from product_supplierinfo ps
						inner join kw_product_price kw on ps.id = kw.supp_info_id
						and ps.name = sp.paying_agent_id
						and ps.customer_id = sp.partner_id
						and ef_date <= sm.delivery_date
						and ps.product_id = sm.product_id
						order by ef_date desc limit 1) as price_unit

					, sm.price_unit as line_price
					, case when sp.state = 'freight_paid' then -sp.freight_balance else 0 end as freight_balance
					, rp.name as supp_name
				from stock_picking sp
				inner join stock_move sm on sm.picking_id = sp.id
				inner join product_product p on p.id = sm.product_id
				inner join res_partner rp on rp.id = sp.paying_agent_id
				--inner join tmp_cycle tc on tc.partner_id = rp.id
				where sp.create_date::date <=now()::date
				and sp.create_date::date >= (select date_start from account_fiscalyear where date_start <= now()::date and date_stop >=now()::date order by id desc limit 1)
				and sp.state not in ('draft','cancel')
				and invoice_line_id is null
				and finvoice_line_id is null
				AND rp.name not ilike '%Kingswood%'
				and rp.supplier is true and rp.handling_charges is false
				and sp.paying_agent_id = part_id
				order by sp.paying_agent_id
				)
			union all
			(
			select sp.name as dc_no
				, sp.date
				, sp.state
				, sp.partner_id as partner_id
				, sm.product_qty as qty
				,0 as fre_total
				, (	select
						case when kw.product_price is not null
						then kw.product_price + (case when kw.transport_price is not null then kw.transport_price else 0 end)  else 0 end
					from product_supplierinfo ps
					inner join kw_product_price kw on ps.id = kw.supp_info_id
					and ps.name = sp.partner_id
					and ps.depot = sm.location_dest_id
					and ef_date <= sm.delivery_date
					and ps.product_id = sm.product_id
					order by ef_date desc limit 1) as price_unit

				, pt.list_price as line_price
				, 0 as freight_balance
				, rp.name as supp_name

			from stock_picking sp
			inner join stock_move sm on sm.picking_id = sp.id
			inner join product_product p on p.id = sm.product_id
			inner join product_template pt on pt.id = p.product_tmpl_id
			inner join res_partner rp on rp.id = sp.partner_id
			--inner join tmp_cycle tc on tc.partner_id = rp.id
			where sp.create_date::date <=now()::date
			and sp.create_date::date >= (select date_start from account_fiscalyear where date_start <= now()::date and date_stop >=now()::date order by id desc limit 1)
			and sp.state in ('done')
			and sp.type = 'in'
			and invoice_line_id is null
			and finvoice_line_id is null
			and sp.sup_invoice is false
			AND rp.name not ilike '%Kingswood%'
			and rp.supplier is true and rp.handling_charges is false
			and sp.paying_agent_id = part_id
			order by sp.partner_id
			)
		)a
		--group by a.supp_name,a.partner_id
		--order by a.partner_id

	)


	union all
		(
			select
					part_id as partner_id
					, (select name from res_partner where id = part_id) as supp_name
					, v1.amount as debit
					, 0 as credit
					, 0 as estimated_amt
				from account_voucher v1
				--inner join res_partner rp1 on rp1.id = v1.partner_id
				inner join res_country_state rs on rs.id = (select state_id from res_partner where id = part_id)
				--inner join tmp_cycle tc on tc.partner_id = rp1.id
				where v1.type in ('payment','sale')
				and v1.freight =false
				and amount >0
				and v1.date > e_date::date and v1.date <=now()::date
				and v1.partner_id in (select distinct(partner_id) from tmp_cycle)
		)

	union all
		(
		select
					  part_id as partner_id
					, (select name from res_partner where id = part_id) as supp_name
					, v1.amount as debit
					, 0 as credit
					, 0 as estimated_amt

				from account_voucher v1
				inner join res_partner rp1 on rp1.id = v1.partner_id
				inner join res_country_state rs on rs.id = rp1.state_id
				inner join tmp_cycle tc on tc.partner_id = rp1.id and tc.partner_id = part_id
				where v1.type in ('purchase','receipt')
				and v1.freight =false
				and amount >0
				and v1.date > tc.st_date::date and v1.date <=now()::date
				and v1.partner_id in (select distinct(partner_id) from tmp_cycle)

		)

	)ab
	--group by ab.supp_name, ab.partner_id
	--order by ab.supp_name, ab.partner_id
	)z
	on z.partner_id = zz.partner

group by z.receipt, z.payments, z.estimate
--order by zz.state_name, zz.partner_name

);

	FOR r IN select * from partner_estimate  LOOP
		return next r;
        END LOOP;

--	select * from partner_estimate;
        RETURN;
    END

    $BODY$
  LANGUAGE plpgsql VOLATILE;

  --select * from facilitator_estimate('2014-04-01', 54, 1070, '2017-05-31')